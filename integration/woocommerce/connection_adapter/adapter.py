from base.base import CatalogBase
from woocommerce.services.woocommerce_services import (
    get_client_product,
    list_client_products,
)


class WooCommerceEngine(CatalogBase):
    def __init__(self, client_id: str):
        super().__init__(client_id)  # No token needed!

    def list_products(self, limit: int = None):
        """List products from WooCommerce store"""
        # Directly calls API with Basic Auth
        products = list_client_products(self._client_id, limit)
        return products

    def get_product(self, product_id: int):
        """Get a single product from WooCommerce store"""
        
        return get_client_product(self._client_id, product_id)