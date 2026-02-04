"""WooCommerce API configuration and URL builders."""

from integration.utils.get_integration_orm import get_integration_orm
from api.constants.codes import IntegrationCodes


def get_product_page_url(store_url: str, product_id: int):
    """Build WooCommerce public product page URL."""
    if not store_url or not product_id:
        return None
    clean_store_url = store_url.replace("https://", "").replace("http://", "").strip("/")
    return f"https://{clean_store_url}/?p={product_id}"


def get_variant_page_url(store_url: str, product_id: int, variation_id: int):
    """Build WooCommerce public variant page URL (product page with variation query param)."""
    base = get_product_page_url(store_url=store_url, product_id=product_id)
    if not base or not variation_id:
        return None
    return f"{base}&variation_id={variation_id}"


def get_woo_base_api_url(store_url: str):
    """Build WooCommerce base API URL."""
    if not store_url.startswith(('http://', 'https://')):
        store_url = f"https://{store_url}"
    return f"{store_url.rstrip('/')}/wp-json/wc/v3"


def get_woo_products_url(store_url: str):
    """Build WooCommerce products list URL."""
    base_url = get_woo_base_api_url(store_url)
    return f"{base_url}/products"


def get_woo_product_url(store_url: str, product_id: int):
    """Build WooCommerce single product URL."""
    base_url = get_woo_base_api_url(store_url)
    return f"{base_url}/products/{product_id}"


async def get_woocommerce_webhook_secret(client_id: str):
    """Get WooCommerce webhook secret from integration ORM."""
    integration = await get_integration_orm(IntegrationCodes.WOOCOMMERCE, client_id)
    return integration.webhook_secret
