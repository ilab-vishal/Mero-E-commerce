"""Shopify integration engine - no database dependencies."""

from base import CatalogBase
from ..services.shopify_services import get_access_token, list_client_products, get_client_product, get_connection_test_results


class ShopifyEngine(CatalogBase):
    """
    Shopify integration engine.
    
    Requires integration_data dict with:
        - client_id: str
        - store_url: str
        - integration_key: str (decrypted)
        - integration_secret: str (decrypted)
        - webhook_secret: str (decrypted, optional)
    """
    
    def __init__(self, integration_data: dict):
        """Initialize with integration data dict."""
        self._integration_data = integration_data
        self._client_id = integration_data.get("client_id")
        self._access_token = None
        self._access_token_expires_in = None
        super().__init__(self._client_id)
    
    def _get_access_token(self):
        """Fetch and cache access token."""
        if self._access_token is None or self._access_token_expires_in is None:
            access_credentials = get_access_token(self._integration_data)
            self._access_token = access_credentials.get("access_token")
            self._access_token_expires_in = access_credentials.get("expires_in")

    def test_connection(self):
        """
        Test connection to Shopify by fetching product count.
        Returns dict with count and optional error.
        """
        connection_data = get_connection_test_results(self._integration_data)
        return connection_data
        
    def list_products(self, limit: int = None):
        """List products from Shopify store."""
        self._get_access_token()
        products = list_client_products(self._integration_data, self._access_token, limit)
        return products

    def get_product(self, product_id: int):
        """Get a single product from Shopify store."""
        self._get_access_token()
        return get_client_product(self._integration_data, self._access_token, product_id)