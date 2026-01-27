# ============================================================
# BULK SYNC ROUTER
# Endpoint to bulk fetch WooCommerce products and index to ES
# ============================================================

import time
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from requests.auth import HTTPBasicAuth
import requests

from woocommerce.config import (
    WOOCOMMERCE_CONSUMER_KEY,
    WOOCOMMERCE_CONSUMER_SECRET,
    WOOCOMMERCE_STORE_URL,
    WOOCOMMERCE_API_VERSION,
)
from woocommerce.services.elasticsearch_service import es_service
from utils.woocommerce_store import handle_parent_product, handle_variant_product, get_product

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/woocommerce", tags=["WooCommerce Bulk Sync"])


class BulkSyncRequest(BaseModel):
    """Request model for bulk sync endpoint."""
    store_url: Optional[str] = None
    consumer_key: Optional[str] = None
    consumer_secret: Optional[str] = None
    per_page: int = 100  # Max products per page (WooCommerce limit is 100)


class BulkSyncResponse(BaseModel):
    """Response model for bulk sync endpoint."""
    status: str
    total_fetched: int
    indexed_count: int
    failed_count: int
    failures: list
    duration_seconds: float


def _build_products_url(store_url: str, page: int, per_page: int) -> str:
    """Build WooCommerce products API URL with pagination."""
    # Clean up the URL
    if not store_url.startswith(('http://', 'https://')):
        store_url = f"http://{store_url}"
    
    base_url = store_url.rstrip('/')
    api_version = WOOCOMMERCE_API_VERSION or "wc/v3"
    
    return f"{base_url}/wp-json/{api_version}/products?page={page}&per_page={per_page}"


def _fetch_all_products(store_url: str, consumer_key: str, consumer_secret: str, per_page: int) -> tuple:
    """
    Fetch all products from WooCommerce with pagination.
    Uses query parameter authentication (more reliable through proxies/ngrok).
    Returns (products_list, error_message or None)
    """
    all_products = []
    page = 1
    
    while True:
        url = _build_products_url(store_url, page, per_page)
        # Use query parameter authentication instead of HTTP Basic Auth
        # This is more reliable when accessing through ngrok/proxies
        url_with_auth = f"{url}&consumer_key={consumer_key}&consumer_secret={consumer_secret}"
        
        logger.info(f"Fetching products page {page}: {url}")
        
        try:
            response = requests.get(url_with_auth, timeout=30)
            
            if response.status_code == 401:
                return [], f"Authentication failed (401): {response.text}. Check your consumer_key and consumer_secret."
            
            if response.status_code != 200:
                return [], f"WooCommerce API error: {response.status_code} - {response.text}"
            
            products = response.json()
            
            if not products:
                # No more products, exit pagination loop
                break
            
            all_products.extend(products)
            logger.info(f"Page {page}: fetched {len(products)} products (total: {len(all_products)})")
            
            # Check if we've reached the last page
            total_pages = int(response.headers.get('X-WP-TotalPages', 1))
            if page >= total_pages:
                break
            
            page += 1
            
        except requests.exceptions.Timeout:
            return [], f"Request timeout while fetching page {page}. The store URL may be unreachable."
        except requests.exceptions.ConnectionError as e:
            error_msg = str(e)
            if "localhost" in store_url.lower() or "127.0.0.1" in store_url:
                return [], (
                    f"Connection error to localhost. If WooCommerce is running locally, "
                    f"you need to use ngrok to create a tunnel. "
                    f"Run: ngrok http 80 (or your WooCommerce port), "
                    f"then use the ngrok URL in store_url parameter. "
                    f"Original error: {error_msg}"
                )
            return [], f"Connection error: {error_msg}. Make sure the store URL is accessible."
        except Exception as e:
            return [], f"Error fetching products: {str(e)}"
    
    return all_products, None


def _fetch_variations(store_url: str, consumer_key: str, consumer_secret: str, product_id: int) -> list:
    """
    Fetch all variations for a specific variable product.
    """
    url = f"{store_url.rstrip('/')}/wp-json/wc/v3/products/{product_id}/variations"
    params = {
        "consumer_key": consumer_key,
        "consumer_secret": consumer_secret,
        "per_page": 100  # Max variations per page
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            return response.json()
        logger.warning(f"Failed to fetch variations for product {product_id}: {response.status_code}")
        return []
    except Exception as e:
        logger.error(f"Error fetching variations for product {product_id}: {e}")
        return []


def _process_products_for_indexing(products: list, store_url: str = None, consumer_key: str = None, consumer_secret: str = None) -> list:
    """
    Process raw WooCommerce products into merged format suitable for ES indexing.
    Populates the shared PRODUCT_STORE for consistency with webhooks.
    """
    processed_ids = []
    
    for product in products:
        product_type = product.get("type", "simple")
        product_id = product.get("id")
        
        # 1. Update/Create the parent in PRODUCT_STORE
        handle_parent_product(product)
        
        if product_type == "variable" and store_url and consumer_key:
            # Fetch full variation data
            logger.info(f"Fetching variations for variable product {product_id}...")
            variations = _fetch_variations(store_url, consumer_key, consumer_secret, product_id)
            
            # 2. Update each variant in PRODUCT_STORE
            for variant in variations:
                handle_variant_product(variant)
            
        processed_ids.append(product_id)
    
    # Return complete merged objects from the store
    return [get_product(pid) for pid in processed_ids if get_product(pid)]


@router.post("/bulk-sync", response_model=BulkSyncResponse)
async def bulk_sync_products(request: BulkSyncRequest):
    """
    Bulk fetch all products from WooCommerce and index them into Elasticsearch.
    
    This endpoint is useful for initial data population or re-syncing all products.
    
    - If credentials are not provided, uses values from .env file
    - Handles pagination automatically (fetches all pages)
    - Returns detailed sync report with success/failure counts
    """
    start_time = time.time()
    
    # Use provided credentials or fall back to environment variables
    store_url = request.store_url or WOOCOMMERCE_STORE_URL
    consumer_key = request.consumer_key or WOOCOMMERCE_CONSUMER_KEY
    consumer_secret = request.consumer_secret or WOOCOMMERCE_CONSUMER_SECRET
    per_page = min(request.per_page, 100)  # WooCommerce max is 100
    
    # Validate credentials
    if not store_url:
        raise HTTPException(status_code=400, detail="Store URL is required")
    if not consumer_key or not consumer_secret:
        raise HTTPException(status_code=400, detail="Consumer key and secret are required")
    
    logger.info(f"Starting bulk sync from: {store_url}")
    
    # Check Elasticsearch connection
    if not es_service.check_connection():
        raise HTTPException(
            status_code=503, 
            detail="Elasticsearch is not available. Please ensure it's running."
        )
    
    # Fetch all products from WooCommerce
    products, error = _fetch_all_products(store_url, consumer_key, consumer_secret, per_page)
    
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    if not products:
        return BulkSyncResponse(
            status="completed",
            total_fetched=0,
            indexed_count=0,
            failed_count=0,
            failures=[],
            duration_seconds=round(time.time() - start_time, 2)
        )
    
    # Process products (fetch variations if needed)
    processed_products = _process_products_for_indexing(
        products, 
        store_url=store_url,
        consumer_key=consumer_key,
        consumer_secret=consumer_secret
    )
    
    logger.info(f"Processed {len(processed_products)} products for indexing")
    
    # Bulk index to Elasticsearch
    result = es_service.bulk_index_products(processed_products)
    
    duration = round(time.time() - start_time, 2)
    
    logger.info(
        f"Bulk sync completed: {result['success_count']} indexed, "
        f"{result['failed_count']} failed, took {duration}s"
    )
    
    return BulkSyncResponse(
        status="completed",
        total_fetched=len(products),
        indexed_count=result["success_count"],
        failed_count=result["failed_count"],
        failures=result["failures"][:50],  # Limit failures to first 50
        duration_seconds=duration
    )


@router.get("/bulk-sync/status")
async def get_sync_status():
    """
    Check the status of Elasticsearch and WooCommerce connectivity.
    Useful for pre-flight checks before running bulk sync.
    """
    es_connected = es_service.check_connection()
    
    return {
        "elasticsearch": {
            "status": "connected" if es_connected else "disconnected",
            "index": es_service.index_name if es_connected else None
        },
        "woocommerce": {
            "configured_store_url": WOOCOMMERCE_STORE_URL,
            "has_credentials": bool(WOOCOMMERCE_CONSUMER_KEY and WOOCOMMERCE_CONSUMER_SECRET)
        }
    }
