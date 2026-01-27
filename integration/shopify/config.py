<<<<<<< HEAD
"""
Shopify-specific configuration settings.

This module contains all Shopify-related configuration values,
loaded from environment variables for security.
"""

import os
from dotenv import load_dotenv

load_dotenv()
=======
"""Shopify API configuration and URL builders."""
import os

SHOPIFY_API_VERSION = "2026-01"
SHOPIFY_WEBHOOK_SECRET = os.getenv("SHOPIFY_WEBHOOK_SECRET")

>>>>>>> feature/woocommerce-integration


# Application Settings
APP_NAME: str = os.getenv("APP_NAME", "Shopify Sales Agent")
APP_HOST: str = os.getenv("APP_HOST", "127.0.0.1")
APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
ENV: str = os.getenv("ENV", "development")
DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"


# Logging
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


# Elasticsearch
ELASTICSEARCH_URL: str = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
ES_INDEX_NAME: str = os.getenv("ES_INDEX_NAME", "shopify_products")
ELASTIC_USER: str = os.getenv("ELASTIC_USER", "elastic")
ELASTIC_PASS: str = os.getenv("ELASTIC_PASS", "changeme")

# Kibana
KIBANA_ES_TOKEN: str = os.getenv("KIBANA_ES_TOKEN", "")


# Shopify Store Configuration
SHOPIFY_STORE_URL: str = os.getenv("SHOPIFY_STORE_URL", "")
SHOPIFY_API_VERSION: str = os.getenv("SHOPIFY_API_VERSION", "2024-01")

# OAuth / API Credentials
SHOPIFY_CLIENT_ID: str = os.getenv("SHOPIFY_CLIENT_ID", "")
SHOPIFY_CLIENT_SECRET: str = os.getenv("SHOPIFY_CLIENT_SECRET", "")
SHOPIFY_ACCESS_TOKEN: str = os.getenv("SHOPIFY_ACCESS_TOKEN", "")

# Webhook Security
SHOPIFY_WEBHOOK_SECRET: str = os.getenv("SHOPIFY_WEBHOOK_SECRET", "")

# Default client key (for multi-tenant support)
SHOPIFY_DEFAULT_CLIENT_KEY: str = os.getenv("SHOPIFY_DEFAULT_CLIENT_KEY", "default")


# Ngrok
NGROK_URL: str = os.getenv("NGROK_URL", "")

# URL Builder Functions
def get_admin_api_url(store_url: str = None) -> str:
    """
    Get the Shopify Admin API base URL.

    Args:
        store_url: The Shopify store URL. Defaults to the one in environment.

    Returns:
        The full Admin API base URL string.
    """
    store = store_url or SHOPIFY_STORE_URL
    return f"https://{store}/admin/api/{SHOPIFY_API_VERSION}"


def get_products_url(store_url: str = None) -> str:
    """
    Get the products endpoint URL.

    Args:
        store_url: The Shopify store URL.

    Returns:
        The full products endpoint URL string.
    """
    return f"{get_admin_api_url(store_url)}/products.json"


def get_product_url(product_id: int, store_url: str = None) -> str:
    """
    Get a single product endpoint URL.

    Args:
        product_id: The unique Shopify product ID.
        store_url: The Shopify store URL.

    Returns:
        The full single product endpoint URL string.
    """
    return f"{get_admin_api_url(store_url)}/products/{product_id}.json"


def get_products_count_url(store_url: str = None) -> str:
    """
    Get the product count endpoint URL.

    Args:
        store_url: The Shopify store URL.

    Returns:
        The full product count endpoint URL string.
    """
    return f"{get_admin_api_url(store_url)}/products/count.json"


def get_webhooks_url(store_url: str = None) -> str:
    """
    Get the webhooks endpoint URL.

    Args:
        store_url: The Shopify store URL.

    Returns:
        The full webhooks endpoint URL string.
    """
    return f"{get_admin_api_url(store_url)}/webhooks.json"


def get_graphql_url(store_url: str = None) -> str:
    """
    Get the GraphQL API endpoint URL.

    Args:
        store_url: The Shopify store URL.

    Returns:
        The full GraphQL API endpoint URL string.
    """
    store = store_url or SHOPIFY_STORE_URL
    return f"https://{store}/admin/api/{SHOPIFY_API_VERSION}/graphql.json"
