"""
Shopify routers module.

Contains webhook route handlers for different event types.
"""

from shopify.routers.product_create import router as product_create_router
from shopify.routers.product_update import router as product_update_router
from shopify.routers.product_delete import router as product_delete_router

__all__ = [
    "product_create_router",
    "product_update_router", 
    "product_delete_router",
]
