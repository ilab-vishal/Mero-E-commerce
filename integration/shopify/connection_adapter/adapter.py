"""
Shopify Engine - Connection Adapter.

Implements the CatalogBase interface for Shopify e-commerce platform.
Provides product listing and fetching capabilities with automatic
token management.
"""

from datetime import datetime
from utils.logging import get_logger
from typing import Optional, List, Dict, Any

from base.base import CatalogBase
from shopify.services.shopify_services import (
    get_access_token,
    list_client_products,
    get_client_product,
    get_store_url,
)

logger = get_logger(__name__)


class ShopifyEngine(CatalogBase):
    """
    Shopify implementation of the CatalogBase interface.
    
    Handles authentication, token caching, and provides a clean API
    for interacting with Shopify product catalogs.
    
    Example:
        >>> engine = ShopifyEngine("my_client_id")
        >>> products = engine.list_products(limit=10)
        >>> product = engine.get_product(product_id=123456)
    """
    
    def __init__(self, client_id: str):
        """
        Initialize the Shopify engine.
        
        Args:
            client_id: Unique identifier for the client/store
        """
        self._access_token: Optional[str] = None
        self._access_token_expires_at: Optional[datetime] = None
        super().__init__(client_id)
        logger.debug(f"ShopifyEngine initialized for client: {client_id}")
    
    def _is_token_valid(self) -> bool:
        """
        Check if the current cached token is valid and not expired.
        """
        if not self._access_token:
            return False
        
        if self._access_token_expires_at:
            # Buffer of 60 seconds to prevent edge cases
            return datetime.now() < self._access_token_expires_at
            
        return True

    def _get_access_token(self) -> str:
        """
        Get or refresh the access token.
        
        Lazily fetches the token on first use and automatically refreshes 
        if the current token is expired.
        
        Returns:
            The access token string
            
        Raises:
            ValueError: If no access token is available
        """
        if not self._is_token_valid():
            if self._access_token:
                logger.info(f"Access token for {self._client_id} expired. Refreshing...")
            else:
                logger.debug(f"Fetching initial access token for {self._client_id}...")
            
            credentials = get_access_token(self._client_id)
            self._access_token = credentials.get("access_token")
            self._access_token_expires_at = credentials.get("expires_at")
            
            if not self._access_token:
                raise ValueError(
                    f"No access token available for client: {self._client_id}"
                )
            
            logger.debug(f"Token acquired. Expires at: {self._access_token_expires_at}")
        
        return self._access_token
    
    def list_products(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch a list of products from Shopify.
        
        Args:
            limit: Maximum number of products to retrieve (default: 50, max: 250)
            
        Returns:
            List of product dictionaries from Shopify API
        """
        self._get_access_token()
        
        store_url = get_store_url(self._client_id)
        logger.info(f"Listing products for client {self._client_id} (url={store_url}), limit={limit}")
        products = list_client_products(
            store_url,
            self._access_token,
            limit
        )
        
        return products
    
    def get_product(self, product_id: int) -> Dict[str, Any]:
        """
        Fetch a single product by ID.
        
        Args:
            product_id: The Shopify product ID
            
        Returns:
            Product dictionary from Shopify API
        """
        self._get_access_token()
        
        store_url = get_store_url(self._client_id)
        logger.info(f"Getting product {product_id} for client {self._client_id} (url={store_url})")
        product = get_client_product(
            store_url,
            self._access_token,
            product_id
        )
        
        return product
