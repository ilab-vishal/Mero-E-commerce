from fastapi import APIRouter, Request, Header, HTTPException
import json
from shopify.utils.shopify_router_utils import verify_shopify_webhook, is_duplicate_event
from celery_service.tasks.process_product_create_webhook import process_product_creation_webhook_task

import logging
from api.utils.logging_config import setup_logging
from api.constants.codes import IntegrationCodes

setup_logging()
logger = logging.getLogger("webhook.shopify.product_create")

router = APIRouter()

@router.post("/products/create/{client_id}")
async def product_created(
    request: Request,
    client_id: str,
    x_shopify_hmac_sha256: str = Header(None),
    x_shopify_event_id: str = Header(None)
):
    if x_shopify_event_id and is_duplicate_event(x_shopify_event_id):
        return 200
    
    body = await request.body()
    logger.info("Received webhook request: %s", True if body else False)

    if not x_shopify_hmac_sha256:
        logger.error("Missing HMAC header")
        raise HTTPException(status_code=401, detail="Missing HMAC header")

    if not await verify_shopify_webhook(body, x_shopify_hmac_sha256, client_id):
        logger.error("Invalid webhook signature")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    product = json.loads(body.decode("utf-8"))
    
    logger.info("Processing webhook request: %s", True if product else False)
    # Enqueue Celery task for async processing
    task = process_product_creation_webhook_task.delay(
        client_id=client_id,
        product_data=product,
        provider = IntegrationCodes.SHOPIFY.value
    )

    return 200