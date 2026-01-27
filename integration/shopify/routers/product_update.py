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


@router.post("/products/update")
async def product_updated(
    request: Request,
    x_shopify_hmac_sha256: str = Header(None, alias="X-Shopify-Hmac-Sha256"),
    x_shopify_event_id: str = Header(None, alias="X-Shopify-Event-Id"),
    x_shopify_topic: str = Header(None, alias="X-Shopify-Topic"),
):
    """
    Handle Shopify product update webhook.
    """
    logger.info("🔔 Webhook received: products/update")
    
    if x_shopify_event_id and is_duplicate_event(x_shopify_event_id):
        logger.warning(f"⚠️ Duplicate event - skipping: {x_shopify_event_id}")
        return {"status": "duplicate", "message": "Event already processed"}
    
    body = await request.body()
    
    if not x_shopify_hmac_sha256:
        logger.error("❌ HMAC header missing")
        raise HTTPException(status_code=401, detail="Missing HMAC header")
    
    if not verify_shopify_webhook(body, x_shopify_hmac_sha256):
        logger.error("❌ HMAC verification failed")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    
    try:
        product_data = json.loads(body.decode("utf-8"))
        product_id = product_data.get("id")
        status = (product_data.get("status") or "").lower()
        logger.info(f"Product {product_id} received with status: '{status}'")

        # Handle status logic
        if status != "active":
            logger.info(f"🗑️ Product {product_id} is '{status}' - removing from index")
            es_service.delete_product(product_id)
            return {"status": "removed", "message": f"Product removed because status is {status}"}

        product_doc = transform_shopify_product(product_data)
        
        # Log the transformed data for visibility
        logger.json(f"Transformed Product {product_doc.product_id}", product_doc.dict())
        
        if es_service.index_product(product_doc):
            logger.info(f"✅ Successfully updated product {product_doc.product_id} in Elasticsearch")
        else:
            logger.error(f"❌ Failed to update product {product_doc.product_id} in Elasticsearch")
        
    except Exception as e:
        logger.error(f"❌ Failed to update product: {e}")
        return {"status": "error", "message": str(e)}
    
    if x_shopify_event_id:
        mark_event_processed(x_shopify_event_id)
    
    return {"status": "success", "product_id": product_data.get("id")}
