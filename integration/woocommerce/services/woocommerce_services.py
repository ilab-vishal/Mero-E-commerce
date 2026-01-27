import requests
from requests.auth import HTTPBasicAuth
from config import (
    WOOCOMMERCE_CONSUMER_KEY,
    WOOCOMMERCE_CONSUMER_SECRET,
    get_woo_product_url as get_product_url,
    get_woo_products_url as list_products_url,
    get_woo_base_api_url as get_base_api_url,
)


def _add_auth_params(url: str) -> str:
    """Add WooCommerce credentials to URL params (more reliable than Basic Auth)"""
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}consumer_key={WOOCOMMERCE_CONSUMER_KEY}&consumer_secret={WOOCOMMERCE_CONSUMER_SECRET}"


def list_products(limit: int = None):
    """Fetch list of products from WooCommerce"""
    products_url = list_products_url()
    if not WOOCOMMERCE_CONSUMER_KEY or not WOOCOMMERCE_CONSUMER_SECRET:
        raise ValueError("Missing WooCommerce credentials")
    
    params = {}
    if limit:
        params["per_page"] = limit
    
    url = _add_auth_params(products_url)
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching products: {response.status_code} - {response.text}")
        return None


def test_connection(store_url: str, consumer_key: str, consumer_secret: str):
    """
    Test connection to WooCommerce API using mandatory user-provided credentials.
    Strictly validated in the backend for modularity.
    """
    if not store_url or not consumer_key or not consumer_secret:
        return {
            "status": "error", 
            "message": "Validation Error: Store URL, Consumer Key, and Consumer Secret are all required."
        }
    
    url = store_url
    key = consumer_key
    secret = consumer_secret
    
    # Standardize URL
    if not url.startswith(('http://', 'https://')):
        url = f"http://{url}"
    
    # Construct base API URL
    base_url = f"{url.rstrip('/')}/wp-json/wc/v3/"
    
    # Use query params for auth in test connection too
    test_url = f"{base_url}?consumer_key={key}&consumer_secret={secret}"
    
    try:
        # Increased timeout for local stability
        response = requests.get(test_url, timeout=30)
        if response.status_code == 200:
            return {"status": "success", "data": response.json()}
        else:
            return {
                "status": "error", 
                "message": f"Bridge Failure: {response.status_code} - Unauthorized or Invalid Store URL."
            }
    except Exception as e:
        return {"status": "error", "message": f"Network Error: {str(e)}"}


def get_product(product_id: int):
    """Fetch a single product from WooCommerce"""
    product_url = get_product_url(product_id)
    if not WOOCOMMERCE_CONSUMER_KEY or not WOOCOMMERCE_CONSUMER_SECRET:
        raise ValueError("Missing WooCommerce credentials")
    
    url = _add_auth_params(product_url)
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching product: {response.status_code} - {response.text}")
        return None

def get_store_product_count(store_url: str, consumer_key: str, consumer_secret: str) -> int:
    """
    Fetch the total number of products from the WooCommerce store.
    """
    if not store_url.startswith(('http://', 'https://')):
        store_url = f"http://{store_url}"
    
    url = f"{store_url.rstrip('/')}/wp-json/wc/v3/products"
    params = {
        "consumer_key": consumer_key,
        "consumer_secret": consumer_secret,
        "per_page": 1
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            return int(response.headers.get('X-WP-Total', 0))
        return 0
    except Exception as e:
        print(f"Error fetching store count: {e}")
        return 0