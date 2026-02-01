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
from worker.tasks import enhance_product_description

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
        
        # Determine if we need to fetch missing weights
        # Recent Shopify API versions move weight to InventoryItem, making it null in Product webhooks
        inventory_data = None
        variants = product_data.get("variants", [])
        
        # Check if weights are missing (any variant has null grams)
        needs_enrichment = any(v.get("grams") is None for v in variants)
        
        if needs_enrichment and variants:
            logger.info(f"Enriching weights for product {product_id} (found null weight fields)")
            from shopify.services.shopify_services import get_inventory_weights
            from config import SHOPIFY_ACCESS_TOKEN
            
            # Extract store domain from request headers or use default
            shop_domain = request.headers.get("X-Shopify-Shop-Domain")
            if not shop_domain:
                from config import SHOPIFY_STORE_URL
                shop_domain = SHOPIFY_STORE_URL
                
            inv_ids = [str(v.get("inventory_item_id")) for v in variants if v.get("inventory_item_id")]
            if inv_ids:
                inventory_data = get_inventory_weights(
                    store_url=shop_domain,
                    access_token=SHOPIFY_ACCESS_TOKEN,
                    inventory_item_ids=inv_ids
                )
            else:
                logger.warning(f"Product {product_id} variants have no inventory_item_ids, cannot fetch weights")
        else:
            logger.debug(f"Weight enrichment not requested or no variants for product {product_id}")

        product_doc = transform_shopify_product(product_data, inventory_data=inventory_data)
        
        # Log the transformed data for visibility
        logger.json(f"Transformed Product {product_doc.product_id}", product_doc.dict())
        
        if es_service.index_product(product_doc):
            logger.info(f"✅ Successfully updated product {product_doc.product_id} in Elasticsearch")
            # Trigger background enrichment with standardized ProductDocument
            enhance_product_description.delay(product_doc.dict())
        else:
            logger.error(f"❌ Failed to update product {product_doc.product_id} in Elasticsearch")
        
    except Exception as e:
        logger.error(f"❌ Failed to update product: {e}")
        return {"status": "error", "message": str(e)}
    
    if x_shopify_event_id:
        mark_event_processed(x_shopify_event_id)
    
    return {"status": "success", "product_id": product_data.get("id")}
