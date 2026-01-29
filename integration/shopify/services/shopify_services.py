from datetime import datetime, timedelta
from utils.logging import get_logger
import requests
from typing import Optional, Dict, Any, List

from config import (
    SHOPIFY_ACCESS_TOKEN,
    SHOPIFY_STORE_URL,
    SHOPIFY_API_VERSION,
    get_shopify_products_url as get_products_url,
    get_shopify_product_url as get_product_url,
    get_shopify_products_count_url as get_products_count_url,
    get_shopify_webhooks_url as get_webhooks_url,
)

logger = get_logger(__name__)


# Store mapping for multi-tenant support
_store_urls: Dict[str, str] = {
    "default": SHOPIFY_STORE_URL,
}

# Access tokens per client (for multi-tenant)
_access_tokens: Dict[str, str] = {
    "default": SHOPIFY_ACCESS_TOKEN,
}


def get_store_url(client_id: str) -> str:
    """
    Get the store URL for a given client.

    Args:
        client_id: The client identifier.

    Returns:
        The Shopify store URL string.
    """
    return _store_urls.get(client_id, SHOPIFY_STORE_URL)


def _get_headers(access_token: str) -> Dict[str, str]:
    """
    Build request headers with authentication.

    Args:
        access_token: Shopify API access token.

    Returns:
        A dictionary of headers for requests.
    """
    return {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json",
    }


def get_access_token(integration_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get access credentials for a client.
    
    Args:
        integration_data: Dictionary containing integration settings.
        
    Returns:
        Dictionary with access_token and expires_in (None for non-expiring tokens)
    """
    client_id = integration_data.get("client_id", "default")
    token = integration_data.get("access_token") or _access_tokens.get(client_id, SHOPIFY_ACCESS_TOKEN)
    
    if not token:
        logger.warning(f"No access token found for client: {client_id}")
        return {"access_token": None, "expires_in": None}
    
    # Shopify Admin API tokens don't usually expire
    expires_in = None 
    
    return {
        "access_token": token,
        "expires_in": expires_in, 
    }


def get_connection_test_results(integration_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Test connection to Shopify and return results.
    
    Args:
        integration_data: Dictionary containing integration settings.
        
    Returns:
        Dictionary with status and message/count.
    """
    store_url = integration_data.get("store_url")
    access_token = integration_data.get("access_token")
    
    if not store_url or not access_token:
        return {
            "status": "error",
            "message": "Missing store_url or access_token in integration data"
        }
        
    try:
        count = get_client_product_count(store_url, access_token)
        return {
            "status": "success",
            "count": count,
            "message": f"Successfully connected. Found {count} products."
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }



def list_client_products(
    integration_data: Dict[str, Any],
    access_token: str,
    limit: Optional[int] = None,
    page_info: Optional[str] = None
) -> tuple[List[Dict[str, Any]], Optional[str]]:
    """
    Fetch a list of products from Shopify with pagination support.
    
    Args:
        integration_data: Dictionary containing integration settings (must have store_url)
        access_token: Shopify API access token
        limit: Maximum number of products to fetch in this page (max 250)
        page_info: Shopify cursor for the next page (for pagination)
        
    Returns:
        Tuple of (list of product dictionaries, next_page_info string or None)
    """
    store_url = integration_data.get("store_url")
    url = get_products_url(store_url)
    
    params = {}
    
    # If page_info is provided, Shopify ignores other parameters except limit
    if page_info:
        params["page_info"] = page_info
    
    if limit:
        params["limit"] = min(limit, 250)  # Shopify max is 250
    elif not page_info:
        params["limit"] = 50  # Default limit if not provided
    
    try:
        response = requests.get(
            url,
            headers=_get_headers(access_token),
            params=params,
            timeout=30
        )
        response.raise_for_status()
        
        data = response.json()
        products = data.get("products", [])
        
        # Parse Link header for next page
        next_page_info = None
        link_header = response.headers.get("Link")
        if link_header:
            # Format: <url>; rel="next", <url>; rel="previous"
            links = link_header.split(",")
            for link in links:
                if 'rel="next"' in link:
                    # Extract page_info from URL query params
                    import re
                    match = re.search(r"page_info=([^&>]+)", link)
                    if match:
                        next_page_info = match.group(1)
        
        logger.info(f"Fetched {len(products)} products (next_page: {bool(next_page_info)})")
        return products, next_page_info
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch products: {e}")
        raise


def get_client_product_count(
    store_url: str,
    access_token: str
) -> int:
    """
    Fetch the total number of products from Shopify.
    
    Args:
        store_url: The Shopify store URL
        access_token: Shopify API access token
        
    Returns:
        The total product count
    """
    url = get_products_count_url(store_url)
    
    try:
        response = requests.get(
            url,
            headers=_get_headers(access_token),
            timeout=30
        )
        response.raise_for_status()
        
        data = response.json()
        count = data.get("count", 0)
        
        logger.info(f"Total products in store {store_url}: {count}")
        return count
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch product count: {e}")
        raise


def get_client_product_status_breakdown(
    store_url: str,
    access_token: str
) -> dict:
    """
    Fetch product counts grouped by status from Shopify.
    Returns a dict like: {"active": 5, "draft": 2, "archived": 1, "total": 8}
    """
    url = get_products_url(store_url)
    
    # Common Shopify statuses
    statuses = ["active", "draft", "archived"]
    breakdown = {}
    total = 0
    
    for status in statuses:
        try:
            response = requests.get(
                url,
                headers=_get_headers(access_token),
                params={"status": status, "limit": 1},
                timeout=30
            )
            response.raise_for_status()
            
            # Shopify doesn't provide total count in headers like WooCommerce
            # We need to use the count endpoint for each status
            count_url = get_products_count_url(store_url)
            count_response = requests.get(
                count_url,
                headers=_get_headers(access_token),
                params={"status": status},
                timeout=30
            )
            count_response.raise_for_status()
            
            data = count_response.json()
            count = data.get("count", 0)
            
            if count > 0:
                breakdown[status] = count
                total += count
                
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {status} product count: {e}")
            continue
    
    breakdown["total"] = total
    return breakdown


def get_client_product(
    integration_data: Dict[str, Any],
    access_token: str,
    product_id: int
) -> Dict[str, Any]:
    """
    Fetch a single product from Shopify.
    
    Args:
        integration_data: Dictionary containing integration settings (must have store_url)
        access_token: Shopify API access token
        product_id: The product ID to fetch
        
    Returns:
        Product dictionary
    """
    store_url = integration_data.get("store_url")
    url = get_product_url(product_id, store_url)
    
    try:
        response = requests.get(
            url,
            headers=_get_headers(access_token),
            timeout=30
        )
        response.raise_for_status()
        
        data = response.json()
        product = data.get("product", {})
        
        logger.info(f"Fetched product {product_id} for store {store_url}")
        return product
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch product {product_id}: {e}")
        raise


def register_client_webhook(
    store_url: str,
    access_token: str,
    topic: str,
    address: str
) -> Dict[str, Any]:
    """
    Register a webhook topic with Shopify.

    Args:
        store_url: The Shopify store URL.
        access_token: Shopify API access token.
        topic: The webhook topic (e.g., "products/create").
        address: The destination URL for the webhook.

    Returns:
        A dictionary containing the API response.
    """
    url = get_webhooks_url(store_url)
    
    json_body = {
        "webhook": {
            "topic": topic,
            "address": address,
            "format": "json"
        }
    }
    
    try:
        response = requests.post(
            url,
            headers=_get_headers(access_token),
            json=json_body,
            timeout=30
        )
        data = response.json()
        
        if response.status_code == 201:
            logger.info(f"Registered webhook: {topic} at {address}")
        elif response.status_code == 422 and "already been taken" in str(data):
            logger.debug(f"Webhook {topic} already registered at {address}")
        else:
            logger.warning(
                f"Failed to register webhook: {topic}. "
                f"Status: {response.status_code}, Response: {data}"
            )
            
            
        return data
        
    except requests.RequestException as e:
        logger.error(f"Failed to register webhook {topic}: {e}")
        raise


def get_inventory_weights(
    store_url: str,
    access_token: str,
    inventory_item_ids: List[str]
) -> Dict[str, Dict[str, Any]]:
    """
    Fetch weight and weight_unit for a list of inventory item IDs using GraphQL.
    
    Returns a mapping of inventory_item_id -> {"weight": float, "unit": str}
    """
    if not inventory_item_ids:
        return {}

    # Clean store_url - ensure it's just the hostname
    host = store_url.split("//")[-1].split("/")[0]
    url = f"https://{host}/admin/api/{SHOPIFY_API_VERSION}/graphql.json"
    headers = _get_headers(access_token)
    
    # GraphQL query to get inventory item details
    query_parts = []
    for i, item_id in enumerate(inventory_item_ids):
        gid = item_id if item_id.startswith("gid://") else f"gid://shopify/InventoryItem/{item_id}"
        query_parts.append(f"""
            item_{i}: node(id: "{gid}") {{
                ... on InventoryItem {{
                    id
                    measurement {{
                        weight {{
                            value
                            unit
                        }}
                    }}
                }}
            }}
        """)
        
    query = f"query {{ {' '.join(query_parts)} }}"
    
    def normalize_unit(unit: str) -> str:
        u = unit.upper()
        if u == "GRAMS": return "g"
        if u == "KILOGRAMS": return "kg"
        if u == "POUNDS": return "lb"
        if u == "OUNCES": return "oz"
        return unit.lower()

    try:
        response = requests.post(
            url,
            headers=headers,
            json={"query": query},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        if "errors" in data:
            logger.error(f"GraphQL errors while fetching weights: {data['errors']}")
            return {}
            
        results = {}
        nodes = data.get("data", {})
        for key, node in nodes.items():
            if node and "measurement" in node:
                m = node["measurement"]
                if m and m["weight"]:
                    item_id = node["id"].split("/")[-1]
                    results[item_id] = {
                        "weight": m["weight"]["value"],
                        "unit": normalize_unit(m["weight"]["unit"])
                    }
        
        if inventory_item_ids:
            logger.info(f"Successfully fetched items from GraphQL. Found weights for {len(results)} out of {len(inventory_item_ids)} items.")
            if results:
                logger.debug(f"Weight results: {results}")
        
        return results
        
    except Exception as e:
        logger.error(f"Failed to fetch inventory weights via GraphQL: {e}", exc_info=True)
        return {}
