from fastapi import APIRouter

from woocommerce.routers.product_create import router as create_router
from woocommerce.routers.product_delete import router as delete_router
from woocommerce.routers.product_update import router as update_router


router = APIRouter(prefix="/webhooks/woocommerce", tags=["WooCommerce"])

router.include_router(create_router)
router.include_router(update_router)
router.include_router(delete_router)
