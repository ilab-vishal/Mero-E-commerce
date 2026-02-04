from pydantic import BaseModel
from typing import Optional
from base import Integrations
from shopify import ShopifyEngine
from shopify.webhook.shopify import router as SHOPIFY_WEBHOOK_ROUTER

from woocommerce import WooCommerceEngine
from woocommerce.webhook.woocommerce import router as WOOCOMMERCE_WEBHOOK_ROUTER


__all__ = [
    "Integrations", "get_engine", "get_integration_provider",
    "ShopifyEngine",  "SHOPIFY_WEBHOOK_ROUTER", 
    "WooCommerceEngine", "WOOCOMMERCE_WEBHOOK_ROUTER"]


_ENGINE_REGISTRY = {
    Integrations.SHOPIFY.value: ShopifyEngine,
    Integrations.WOOCOMMERCE.value: WooCommerceEngine,
}

class _IntegrationPayload(BaseModel):
    client_id: str
    store_url: str  
    integration_key: str
    integration_secret: str
    provider: str
    webhook_secret: Optional[str] = None

    model_config = {"from_attributes": True}


def get_engine(integration_name: str, integration_payload: _IntegrationPayload):
    """
    Get integration engine instance.
    
    Args:
        integration_name: Name of integration (e.g., "shopify")
        integration_data: Dict with integration credentials and config
            Required keys:
                - client_id: str
                - store_url: str
                - integration_key: str (decrypted)
                - integration_secret: str (decrypted)
                - webhook_secret: str (decrypted, optional)
    
    Returns:
        Engine instance initialized with integration_data
    """
    integration_data = integration_payload
    engine_cls = _ENGINE_REGISTRY.get(integration_name)
    if not engine_cls:
        raise ValueError(f"Unknown integration: {integration_name}")
    return engine_cls(integration_data)

def get_integration_provider():
    return [integration.value for integration in Integrations]