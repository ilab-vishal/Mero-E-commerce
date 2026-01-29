from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from config import SHOPIFY_CLIENT_ID
from shopify.services.shopify_services import get_client_product_status_breakdown
from base.elasticsearch_service import es_service
from shopify.services.product_transformer import transform_shopify_product
from base.models import ProductDocument
from utils.logging import get_logger

router = APIRouter(
    prefix="/api/shopify",
    tags=["Shopify Integration"],
    responses={404: {"description": "Not found"}},
)

logger = get_logger(__name__)


class ConnectionCredentials(BaseModel):
    """
    Schema for store connection credentials.
    """
    platform: str
    client_id: Optional[str] = None
    store_url: str
    access_token: str
    webhook_secret: Optional[str] = None


class SyncResponse(BaseModel):
    """
    Schema for synchronization initiation responses.
    """
    message: str
    status: str


@router.post("/connect")
async def test_connection(creds: ConnectionCredentials):
    """
    Test the connection to the e-commerce platform using provided credentials.
    
    Args:
        creds: The connection credentials including store URL and access token.

    Returns:
        A dictionary indicating connection success and details.

    Raises:
        HTTPException: If the platform is unsupported or connection fails.
    """
    if creds.platform.lower() != "shopify":
        raise HTTPException(
            status_code=400,
            detail="Only Shopify is currently supported."
        )

    client_id = creds.client_id or SHOPIFY_CLIENT_ID
    logger.info(
        f"Testing connection for store: {creds.store_url} (Client ID: {client_id})"
    )
    
    try:
        # Fetch product breakdown by status
        breakdown = get_client_product_status_breakdown(
            store_url=creds.store_url,
            access_token=creds.access_token
        )
        
        total = breakdown.get("total", 0)
        
        # Build status breakdown message
        status_parts = []
        for status in ["active", "draft", "archived"]:
            if status in breakdown and breakdown[status] > 0:
                status_parts.append(f"{breakdown[status]} {status}")
        
        status_message = ", ".join(status_parts) if status_parts else "0"
        
        return {
            "status": "success", 
            "message": "Connection successful!", 
            "details": f"Success! We found {total} product{'s' if total != 1 else ''} in your store ({status_message}). You are ready to start synchronization.",
            "total_store_products": total,
            "product_breakdown": breakdown
        }
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        # Return a user-friendly message instead of technical details
        raise HTTPException(
            status_code=400,
            detail=(
                "Connection failed. Please verify your Store URL and "
                "Admin API Access Token, then try again."
            )
        )


async def background_bulk_sync(store_url: str, access_token: str, client_id: str):
    """
    Background task to fetch all products across multiple pages and index them.

    Args:
        store_url: The Shopify store URL.
        access_token: Shopify API access token.
        client_id: The client identifier for logging.
    """
    try:
        logger.info(f"Starting bulk sync for {store_url} (Client: {client_id})")
        
        total_indexed = 0
        page_info = None
        has_more = True
        
        while has_more:
            # Fetch batch from Shopify (max 250)
            products_batch_data, next_page_info = list_client_products(
                integration_data={"store_url": store_url},
                access_token=access_token,
                limit=250,
                page_info=page_info
            )
            
            if not products_batch_data:
                break
                
            # Transform the batch
            batch_to_index = []
            for product_data in products_batch_data:
                try:
                    product_doc = transform_shopify_product(product_data)
                    batch_to_index.append(product_doc)
                    
                    # Log the transformed data for visibility
                    logger.json(
                        f"Transformed Product {product_doc.product_id}",
                        product_doc.dict()
                    )
                except Exception as item_err:
                    logger.error(
                        f"Failed to adapt product {product_data.get('id')}: "
                        f"{item_err}"
                    )
                    continue
            
            # Use High-Performance Bulk API to index the entire batch at once
            if batch_to_index:
                if es_service.bulk_index_products(batch_to_index):
                    total_indexed += len(batch_to_index)
                    logger.info(
                        f"Successfully bulk indexed {len(batch_to_index)} "
                        f"products (Total: {total_indexed})"
                    )
                else:
                    logger.error(f"Failed to bulk index batch for {store_url}")
            
            # Move to next page
            page_info = next_page_info
            has_more = bool(page_info)
            
        logger.info(
            f"Bulk sync completed. Total indexed: {total_indexed} products."
        )
        
    except Exception as e:
        logger.error(f"Bulk sync critical failure: {e}")


@router.post("/sync", response_model=SyncResponse)
async def trigger_bulk_sync(
    creds: ConnectionCredentials,
    background_tasks: BackgroundTasks
):
    """
    Trigger a bulk sync of products from the platform to Elasticsearch.

    Args:
        creds: The connection credentials.
        background_tasks: FastAPI BackgroundTasks handler.

    Returns:
        A SyncResponse indicating the task has been accepted.

    Raises:
        HTTPException: If the platform is unsupported or credentials are invalid.
    """
    if creds.platform.lower() != "shopify":
        raise HTTPException(
            status_code=400,
            detail="Only Shopify is currently supported."
        )

    # Basic validation first
    try:
         list_client_products({"store_url": creds.store_url}, creds.access_token, limit=1)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid credentials: {str(e)}"
        )

    client_id = creds.client_id or SHOPIFY_CLIENT_ID

    # Add to background tasks
    background_tasks.add_task(
        background_bulk_sync,
        creds.store_url,
        creds.access_token,
        client_id
    )
    
    return SyncResponse(
        status="accepted", 
        message=(
            f"Bulk sync started for client {client_id}. "
            "Check server logs for progress."
        )
    )
