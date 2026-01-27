"""Shopify API configuration and URL builders."""
import os

SHOPIFY_API_VERSION = "2026-01"
SHOPIFY_WEBHOOK_SECRET = os.getenv("SHOPIFY_WEBHOOK_SECRET")



def get_access_token_url(store_url: str):
    """Build Shopify OAuth access token URL."""
    return f"https://{store_url}/admin/oauth/access_token"


def list_products_url(store_url: str):
    """Build Shopify products list URL."""
    return f"https://{store_url}/admin/api/{SHOPIFY_API_VERSION}/products.json"


def get_product_url(store_url: str, product_id: int):
    """Build Shopify single product URL."""
    return f"https://{store_url}/admin/api/{SHOPIFY_API_VERSION}/products/{product_id}.json"


def get_connection_test_url(store_url: str):
    """Build Shopify connection test URL (product count endpoint)."""
    return f"https://{store_url}/admin/api/{SHOPIFY_API_VERSION}/products/count.json"
