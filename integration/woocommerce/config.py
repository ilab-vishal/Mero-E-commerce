import os

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv():
        return False

load_dotenv()

APP_HOST = os.getenv("APP_HOST")
APP_PORT = os.getenv("APP_PORT")

WOOCOMMERCE_API_VERSION = os.getenv("WOOCOMMERCE_API_VERSION")
WOOCOMMERCE_CONSUMER_KEY=os.getenv("WOOCOMMERCE_CONSUMER_KEY")
WOOCOMMERCE_CONSUMER_SECRET=os.getenv("WOOCOMMERCE_CONSUMER_SECRET")
WOOCOMMERCE_WEBHOOK_SECRET=os.getenv("WOOCOMMERCE_WEBHOOK_SECRET")

# Elasticsearch Configuration
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
ELASTICSEARCH_INDEX_NAME = os.getenv("ELASTICSEARCH_INDEX_NAME", "woocommerce-products-v1")
ELASTIC_USER = os.getenv("ELASTIC_USER", "elastic")
ELASTIC_PASS = os.getenv("ELASTIC_PASS", "password")

WOOCOMMERCE_STORE_URL = os.getenv("WOOCOMMERCE_STORE_URL", "localhost/woocommerce_store")


def list_products_url():
    """Build URL for listing products"""
    return f"http://{WOOCOMMERCE_STORE_URL}/wp-json/{WOOCOMMERCE_API_VERSION}/products"


def get_product_url(product_id: int):
    """Build URL for getting a single product"""
    return f"http://{WOOCOMMERCE_STORE_URL}/wp-json/{WOOCOMMERCE_API_VERSION}/products/{product_id}"


def get_base_api_url():
    """Build URL for testing connection (base API endpoint)"""
    return f"http://{WOOCOMMERCE_STORE_URL}/wp-json/{WOOCOMMERCE_API_VERSION}/"