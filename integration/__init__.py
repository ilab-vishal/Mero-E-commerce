"""
E-Commerce Integration Platform - Factory Pattern.

Provides a unified way to instantiate platform-specific engines
using a factory function.
"""

from base.integrations import Integrations
from shopify.connection_adapter.adapter import ShopifyEngine

__all__ = ["ShopifyEngine", "Integrations", "get_engine"]

# Engine registry - maps integration names to their engine classes
_ENGINE_REGISTRY = {
    Integrations.SHOPIFY.value: ShopifyEngine,
    # Add new integrations here:
    # Integrations.MAGENTO.value: MagentoEngine,
}


def get_engine(integration_name: str, integration_data: Dict[str, Any]):
    """
    Factory function to create platform-specific engine instances.

    Args:
        integration_name: The platform identifier (e.g., "shopify", "woocommerce")
        integration_data: Dictionary containing integration settings and credentials
    Returns:
        An instance of the appropriate engine (e.g., ShopifyEngine)
    Raises:
        ValueError: If the integration name is not supported
    Example:
        >>> data = {"client_id": "c1", "store_url": "shop.myshopify.com", "access_token": "tk_123"}
        >>> engine = get_engine("shopify", data)
        >>> products = engine.list_products(limit=10)
    """
    engine_cls = _ENGINE_REGISTRY.get(integration_name)
    if engine_cls is None:
        supported = ", ".join(_ENGINE_REGISTRY.keys())
        raise ValueError(
            f"Unknown integration: '{integration_name}'. "
            f"Supported integrations: {supported}"
        )
    return engine_cls(integration_data)

