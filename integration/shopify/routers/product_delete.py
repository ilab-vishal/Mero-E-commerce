from fastapi import APIRouter, HTTPException, Request, Header
from utils.logging import get_logger
from shopify.utils.shopify_router_utils import (
    verify_shopify_webhook,
    is_duplicate_event,
    mark_event_processed,
)
from base.elasticsearch_service import es_service

logger = get_logger(__name__)
router = APIRouter()


@router.post("/products/delete")
async def product_deleted(
    request: Request,
    x_shopify_hmac_sha256: str = Header(None, alias="X-Shopify-Hmac-Sha256"),
    x_shopify_event_id: str = Header(None, alias="X-Shopify-Event-Id"),
    x_shopify_topic: str = Header(None, alias="X-Shopify-Topic"),
):
    """
    Handle Shopify product deletion webhook.
    """
    logger.info("🔔 Webhook received: products/delete")
    
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
    
    # Payload for delete events only contains the product ID
    try:
        data = await request.json()
        product_id = str(data.get("id"))
    except Exception as e:
        logger.error(f"❌ Failed to parse delete webhook body: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    if es_service.delete_product(product_id):
        logger.info(f"🗑️ Successfully deleted product {product_id} from Elasticsearch")
    else:
        logger.error(f"❌ Failed to delete product {product_id} from Elasticsearch")
    
    if x_shopify_event_id:
        mark_event_processed(x_shopify_event_id)
    
    return {"status": "success", "product_id": product_id}
