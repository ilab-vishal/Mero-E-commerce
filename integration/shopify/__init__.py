"""
Shopify Integration Module.

This module provides:
- ShopifyEngine: Adapter for Shopify API operations
- Webhook handlers: For product create/update/delete events
- Configuration: Shopify-specific settings
"""

from shopify.connection_adapter import ShopifyEngine
from shopify.webhook import router as webhook_router

__all__ = ["ShopifyEngine", "webhook_router"]
