"""
E-Commerce Integration Platform - Factory Pattern.

Provides a unified way to instantiate platform-specific engines
using a factory function.
"""

from typing import Dict, Any, Type
from base.integrations import Integrations
from base.base import CatalogBase
from shopify.connection_adapter.adapter import ShopifyEngine
from woocommerce.connection_adapter.adapter import WooCommerceEngine

# Engine registry - maps integration names to their engine classes
_ENGINE_REGISTRY: Dict[str, Type[CatalogBase]] = {
    Integrations.SHOPIFY.value: ShopifyEngine,
    Integrations.WOOCOMMERCE.value: WooCommerceEngine,
}

__all__ = ["ShopifyEngine", "WooCommerceEngine", "Integrations", "get_engine"]

def get_engine(integration_name: str, integration_data: Dict[str, Any]) -> CatalogBase:
    """
    Factory function to create platform-specific engine instances.

    Args:
        integration_name: The platform identifier (e.g., "shopify", "woocommerce")
        integration_data: Dictionary containing integration settings and credentials
    Returns:
        An instance of the appropriate engine (e.g., ShopifyEngine)
    Raises:
        ValueError: If the integration name is not supported
    """
    engine_cls = _ENGINE_REGISTRY.get(integration_name)
    if engine_cls is None:
        supported = ", ".join(_ENGINE_REGISTRY.keys())
        raise ValueError(
            f"Unknown integration: '{integration_name}'. "
            f"Supported integrations: {supported}"
        )
    return engine_cls(integration_data)
