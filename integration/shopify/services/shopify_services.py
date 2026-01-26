"""Shopify API service functions - no database dependencies."""

import requests
from shopify.config import (
    get_access_token_url,
    get_product_url,
    list_products_url,
    get_connection_test_url
)


def get_access_token(integration_data: dict):
    """
    Get Shopify access token using integration credentials.
    
    Args:
        integration_data: Dict with keys: store_url, integration_key, integration_secret
    """
    store_url = integration_data.get("store_url")
    integration_key = integration_data.get("integration_key")
    integration_secret = integration_data.get("integration_secret")
    
    if not store_url:
        raise ValueError("Missing store_url in integration_data")
    if not integration_key or not integration_secret:
        raise ValueError("Missing Shopify credentials in integration_data")

    access_token_url = get_access_token_url(store_url)
    json_body = {
        "client_id": integration_key,
        "client_secret": integration_secret,
        "grant_type": "client_credentials" 
    }

    response = requests.post(access_token_url, json=json_body)
    if response.status_code == 200:
        access_information = response.json()
        return {
            "access_token": access_information.get("access_token"),
            "expires_in": access_information.get("expires_in")
        }
    else:
        return {
            "access_token": None,
            "expires_in": None
        }


def list_client_products(integration_data: dict, access_token: str, limit: int = None):
    """
    List Shopify products for a store.
    
    Args:
        integration_data: Dict with key: store_url
        access_token: Shopify access token
        limit: Max number of products to return
    """
    store_url = integration_data.get("store_url")
    if not store_url:
        raise ValueError("Missing store_url in integration_data")
    
    products_url = list_products_url(store_url)
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": access_token
    }
    params = {"limit": limit} if limit else {}
    
    response = requests.get(products_url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return None


def get_client_product(integration_data: dict, access_token: str, product_id: int):
    """
    Get a single Shopify product.
    
    Args:
        integration_data: Dict with key: store_url
        access_token: Shopify access token
        product_id: Shopify product ID
    """
    store_url = integration_data.get("store_url")
    if not store_url:
        raise ValueError("Missing store_url in integration_data")
    
    product_url = get_product_url(store_url, product_id)
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": access_token
    }
    
    response = requests.get(product_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None


def get_connection_test_results(integration_data: dict):
    """
    Test Shopify connection by fetching product count.
    
    Args:
        integration_data: Dict with keys: store_url, integration_key, integration_secret
    """
    try:
        store_url = integration_data.get("store_url")
        if not store_url:
            raise ValueError("Missing store_url in integration_data")
        
        # Get access token first
        access_token_data = get_access_token(integration_data)
        access_token = access_token_data.get("access_token")
        
        if not access_token:
            return {"count": None, "error": "Failed to get access token"}
        
        connection_test_url = get_connection_test_url(store_url)
        headers = {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": access_token
        }
        response = requests.get(connection_test_url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return {"count": None, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"count": None, "error": str(e)}
