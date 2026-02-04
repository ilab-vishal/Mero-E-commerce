"""Shopify API configuration and URL builders."""

from integration.utils.get_integration_orm import get_integration_orm
from api.constants.codes import IntegrationCodes

SHOPIFY_API_VERSION = "2026-01"


def get_product_page_url(store_url: str, handle: str):
    """Build Shopify public product page URL."""
    if not store_url or not handle:
        return None
    clean_store_url = store_url.replace("https://", "").replace("http://", "").strip("/")
    clean_handle = str(handle).strip("/")
    return f"https://{clean_store_url}/products/{clean_handle}"


def get_variant_page_url(store_url: str, handle: str, variant_id: int):
    """Build Shopify public variant page URL (product page with variant query param)."""
    base = get_product_page_url(store_url=store_url, handle=handle)
    if not base or not variant_id:
        return None
    return f"{base}?variant={variant_id}"

def get_access_token_url(store_url: str):
    """Build Shopify OAuth access token URL."""
    return f"https://{store_url}/admin/oauth/access_token"


def list_products_url(store_url: str):
    """Build Shopify products list URL."""
    return f"https://{store_url}/admin/api/{SHOPIFY_API_VERSION}/products.json"


def get_product_url(store_url: str, product_id: int):
    """Build Shopify single product URL."""
    return f"https://{store_url}/admin/api/{SHOPIFY_API_VERSION}/products/{product_id}.json"


def get_products_count_url(store_url: str):
    """Build Shopify connection test URL (product count endpoint)."""
    return f"https://{store_url}/admin/api/{SHOPIFY_API_VERSION}/products/count.json"


async def get_shopify_webhook_secret(client_id: str):

    integration = await get_integration_orm(IntegrationCodes.SHOPIFY, client_id)
    return integration.webhook_secret
