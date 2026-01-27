"""
Shopify Webhook Router Aggregator.

Combines all product webhook handlers into a single router
with appropriate prefixing and tagging.
"""

from fastapi import APIRouter

from shopify.routers.product_create import router as create_router
from shopify.routers.product_update import router as update_router
from shopify.routers.product_delete import router as delete_router

# Main Shopify webhook router
router = APIRouter(
    prefix="/webhooks/shopify",
    tags=["Shopify Webhooks"],
)

# Include individual event routers
router.include_router(create_router)
router.include_router(update_router)
router.include_router(delete_router)
