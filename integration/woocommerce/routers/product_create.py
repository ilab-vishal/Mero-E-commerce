import json

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from woocommerce.utils.woocommerce_store import (
    get_product,
    handle_parent_product,
    handle_variant_product,
)
from utils.logging import get_logger
from base.elasticsearch_service import es_service
from worker.tasks import enhance_product_description
from woocommerce.services.woocommerce_services import (
    get_product as fetch_remote_product,
    get_product_variations,
)
from woocommerce.utils.product_transformer import transform_product_for_es
from woocommerce.utils.webhook_guard import is_woocommerce_ping
from woocommerce.utils.woocommerce_router_utils import (
    is_duplicate_event,
    verify_woocommerce_webhook,
)

router = APIRouter()
logger = get_logger("product_create")


@router.post("/products/create")
async def product_created(
    request: Request,
    x_wc_webhook_signature: str = Header(None),
    x_wc_webhook_id: str = Header(None),
    x_wc_webhook_topic: str = Header(None),
):
    logger.info(
        "Received WooCommerce product create webhook",
        extra={"topic": x_wc_webhook_topic},
    )

    # Read body
    body_bytes = await request.body()

    if is_woocommerce_ping(x_wc_webhook_topic, body_bytes):
        logger.info("Ping received", extra={"topic": x_wc_webhook_topic})
        return {"status": "pong"}

    # Signature validation
    if not x_wc_webhook_signature or not verify_woocommerce_webhook(
        body_bytes, x_wc_webhook_signature
    ):
        logger.warning("Invalid webhook signature", extra={"topic": x_wc_webhook_topic})
        raise HTTPException(status_code=401, detail="Invalid webhook")

    # Parse payload
    product = json.loads(body_bytes.decode("utf-8"))
    product_id = product.get("id")

    # Deduplication
    if x_wc_webhook_id and is_duplicate_event(x_wc_webhook_id, product_id):
        logger.info(
            "Duplicate event ignored",
            extra={"product_id": product_id, "event_id": x_wc_webhook_id},
        )
        return JSONResponse(status_code=200, content={"status": "duplicate"})

    # Merge product and index in Elasticsearch
    if product.get("type") == "variation":
        logger.info(f"Processing variation product: ID={product_id}")
        handle_variant_product(product)
        parent_id = product.get("parent_id")
        merged = get_product(parent_id)
        if merged:
            try:
                logger.info(
                    f"Indexing parent product after variant update: ParentID={parent_id}, VariantID={product_id}"
                )
                product_doc = transform_product_for_es(merged)
                if es_service.index_product(product_doc):
                    enhance_product_description.delay(product_doc.dict())
                logger.info(
                    "Successfully indexed parent product after variant create",
                    extra={"parent_id": parent_id, "variant_id": product_id},
                )
            except Exception as e:
                logger.error(
                    "Elasticsearch indexing failed for parent product (variant trigger)",
                    extra={"error": str(e), "parent_id": parent_id},
                )
        else:
            logger.warning(
                f"Parent product not found for variant: VariantID={product_id}, ParentID={parent_id}"
            )

    else:
        logger.info(f"Processing simple/variable product: ID={product_id}")
        merged = handle_parent_product(product)

        # If variable product, fetch and update all variations (same as update logic)
        if product.get("type") == "variable":
            logger.info(
                f"Fetching variations for created parent product: ID={product_id}"
            )
            try:
                variations = get_product_variations(product_id)
                for variant_data in variations:
                    handle_variant_product(variant_data)
            except Exception as e:
                logger.error(
                    f"Error fetching variations for parent creation: {e}",
                    extra={"product_id": product_id},
                )

        if merged:
            try:
                logger.info(f"Indexing product: ID={product_id}")
                product_doc = transform_product_for_es(merged)
                if es_service.index_product(product_doc):
                    enhance_product_description.delay(product_doc.dict())
                logger.info(
                    "Successfully indexed product in ES",
                    extra={"product_id": product_id},
                )
            except Exception as e:
                logger.error(
                    "Elasticsearch indexing failed for product",
                    extra={"error": str(e), "product_id": product_id},
                )
        else:
            logger.warning(
                f"Product processing returned None (possibly ignored or failed), ID={product_id}"
            )

    return {"status": "success", "product_id": product_id}
