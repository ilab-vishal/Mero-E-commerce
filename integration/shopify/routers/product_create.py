import json
from fastapi import APIRouter, HTTPException, Request, Header
from utils.logging import get_logger

from shopify.utils.shopify_router_utils import (
    verify_shopify_webhook,
    is_duplicate_event,
    mark_event_processed,
)
from shopify.services.product_transformer import transform_shopify_product
from base.elasticsearch_service import es_service

logger = get_logger(__name__)
router = APIRouter()


@router.post("/products/create")
async def product_created(
    request: Request,
    x_shopify_hmac_sha256: str = Header(None, alias="X-Shopify-Hmac-Sha256"),
    x_shopify_event_id: str = Header(None, alias="X-Shopify-Event-Id"),
    x_shopify_topic: str = Header(None, alias="X-Shopify-Topic"),
):
    """
    Handle Shopify product creation webhook.
    """
    logger.info("Webhook received: products/create")

    if x_shopify_event_id and is_duplicate_event(x_shopify_event_id):
        logger.warning(f"Duplicate event - skipping: {x_shopify_event_id}")
        return {"status": "duplicate", "message": "Event already processed"}

    body = await request.body()

    if not x_shopify_hmac_sha256:
        logger.error("HMAC header missing")
        raise HTTPException(status_code=401, detail="Missing HMAC header")

    if not verify_shopify_webhook(body, x_shopify_hmac_sha256):
        logger.error("HMAC verification failed")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        product_data = json.loads(body.decode("utf-8"))
        
        # Only process active products
        status = (product_data.get("status") or "").lower()
        logger.info(f"Product {product_data.get('id')} received with status: '{status}'")
        if status != "active":
            logger.info(f"Skipping product {product_data.get('id')} - Status is '{status}' (expected 'active')")
            return {"status": "skipped", "message": f"Product status is {status}"}

        product_doc = transform_shopify_product(product_data)
        
        # Log the transformed data for visibility
        logger.json(f"Transformed Product {product_doc.product_id}", product_doc.dict())
        
        if es_service.index_product(product_doc):
            logger.info(f"Successfully indexed product {product_doc.product_id}")
        else:
            logger.error(f"Failed to index product {product_doc.product_id}")
        
    except Exception as e:
        logger.error(f"Failed to process product: {e}")
        return {"status": "error", "message": str(e)}
    
    if x_shopify_event_id:
        mark_event_processed(x_shopify_event_id)
    
    return {"status": "success", "product_id": product_data.get("id")}
