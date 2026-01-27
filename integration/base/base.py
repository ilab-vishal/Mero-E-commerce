"""
Abstract base class for e-commerce catalog integrations.

All platform-specific engines (ShopifyEngine, WooCommerceEngine, etc.)
must extend this class and implement required methods.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class CatalogBase(ABC):
    """
    Abstract base class for e-commerce platform catalog operations.

    Provides a unified interface for interacting with product catalogs
    across different e-commerce platforms.

    Attributes:
        _client_id: Unique identifier for the client/store
    """

    def __init__(self, client_id: str):
        """
        Initialize the catalog base with a client identifier.

        Args:
            client_id: Unique identifier for the client/store
        """
        self._client_id = client_id

    @property
    def client_id(self) -> str:
        """Get the client identifier."""
        return self._client_id

    @abstractmethod
    def list_products(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch a list of products from the catalog.

        Args:
            limit: Maximum number of products to retrieve (optional)

        Returns:
            List of product dictionaries

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement list_products()")

    @abstractmethod
    def get_product(self, product_id: int) -> Dict[str, Any]:
        """
        Fetch a single product by its ID.

        Args:
            product_id: The unique identifier of the product

        Returns:
            Product dictionary

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement get_product()")
