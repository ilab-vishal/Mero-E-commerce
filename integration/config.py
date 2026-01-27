"""
Unified configuration settings for Shopify and WooCommerce integrations.
Provides a central location for API versions, URLs, and shared service settings.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Application Settings ---
APP_NAME: str = os.getenv("APP_NAME", "Mero E-commerce Integration")
APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# --- Shopify Specific Configuration ---
SHOPIFY_STORE_URL: str = os.getenv("SHOPIFY_STORE_URL", "")
SHOPIFY_API_VERSION: str = os.getenv("SHOPIFY_API_VERSION", "2026-01")
SHOPIFY_CLIENT_ID: str = os.getenv("SHOPIFY_CLIENT_ID", "")
SHOPIFY_CLIENT_SECRET: str = os.getenv("SHOPIFY_CLIENT_SECRET", "")
SHOPIFY_ACCESS_TOKEN: str = os.getenv("SHOPIFY_ACCESS_TOKEN", "")
SHOPIFY_WEBHOOK_SECRET: str = os.getenv("SHOPIFY_WEBHOOK_SECRET", "")

# --- WooCommerce Specific Configuration ---
WOOCOMMERCE_STORE_URL: str = os.getenv("WOOCOMMERCE_STORE_URL", "")
WOOCOMMERCE_API_VERSION: str = os.getenv("WOOCOMMERCE_API_VERSION", "wc/v3")
WOOCOMMERCE_CONSUMER_KEY: str = os.getenv("WOOCOMMERCE_CONSUMER_KEY", "")
WOOCOMMERCE_CONSUMER_SECRET: str = os.getenv("WOOCOMMERCE_CONSUMER_SECRET", "")
WOOCOMMERCE_WEBHOOK_SECRET: str = os.getenv("WOOCOMMERCE_WEBHOOK_SECRET", "")

# --- Shared Services ---
ELASTICSEARCH_URL: str = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")
ES_INDEX_NAME: str = os.getenv("ES_INDEX_NAME", "ecommerce_unified")
ELASTIC_USER: str = os.getenv("ELASTIC_USER", "elastic")
ELASTIC_PASS: str = os.getenv("ELASTIC_PASS", "changeme")
KIBANA_ES_TOKEN: str = os.getenv("KIBANA_ES_TOKEN", "")
NGROK_URL: str = os.getenv("NGROK_URL", "")


# --- URL Helper Functions (Shopify) ---
def get_shopify_admin_api_url(store_url: str = None) -> str:
    store = store_url or SHOPIFY_STORE_URL
    return f"https://{store}/admin/api/{SHOPIFY_API_VERSION}"

def get_shopify_products_url(store_url: str = None) -> str:
    return f"{get_shopify_admin_api_url(store_url)}/products.json"

def get_shopify_product_url(product_id: int, store_url: str = None) -> str:
    return f"{get_shopify_admin_api_url(store_url)}/products/{product_id}.json"

def get_shopify_products_count_url(store_url: str = None) -> str:
    return f"{get_shopify_admin_api_url(store_url)}/products/count.json"

def get_shopify_webhooks_url(store_url: str = None) -> str:
    return f"{get_shopify_admin_api_url(store_url)}/webhooks.json"


# --- URL Helper Functions (WooCommerce) ---
def get_woo_base_api_url(store_url: str = None) -> str:
    store = store_url or WOOCOMMERCE_STORE_URL
    if not store.startswith(('http://', 'https://')):
        store = f"http://{store}"
    return f"{store.rstrip('/')}/wp-json/{WOOCOMMERCE_API_VERSION}"

def get_woo_products_url(store_url: str = None) -> str:
    return f"{get_woo_base_api_url(store_url)}/products"

def get_woo_product_url(product_id: int, store_url: str = None) -> str:
    return f"{get_woo_base_api_url(store_url)}/products/{product_id}"