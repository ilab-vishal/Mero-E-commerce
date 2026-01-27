import json

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from utils.woocommerce_store import (
    get_all_products,
    get_product,
    handle_product_delete,
)
from woocommerce.loggers import get_logger
from base.elasticsearch_service import es_service
from woocommerce.utils.webhook_guard import is_woocommerce_ping
from woocommerce.utils.product_transformer import transform_product_for_es
from woocommerce.utils.woocommerce_router_utils import (
    is_duplicate_event,
    verify_woocommerce_webhook,
)

router = APIRouter()
logger = get_logger("product_delete")


@router.post("/products/delete")
async def product_deleted(
    request: Request,
    x_wc_webhook_signature: str = Header(None),
    x_wc_webhook_id: str = Header(None),
    x_wc_webhook_topic: str = Header(None),
):
    logger.info(
        "Received WooCommerce product delete webhook",
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

    # Handle delete
    if product.get("type") == "variation":
        parent_id = product.get("parent_id")
        logger.info(
            f"Processing variation delete: ID={product_id}, ParentID={parent_id}"
        )
        handle_product_delete(product)
        merged = get_product(parent_id)
        if merged:
            try:
                product_doc = transform_product_for_es(merged)
                es_service.index_product(product_doc)
                logger.info(
                    "Parent re-indexed after variant delete",
                    extra={"parent_id": parent_id, "variant_id": product_id},
                )
            except Exception as e:
                logger.error(
                    "Elasticsearch re-index failed for parent",
                    extra={"error": str(e), "parent_id": parent_id},
                )
        else:
            logger.warning(
                "Parent product not found after variant delete",
                extra={"parent_id": parent_id, "variant_id": product_id},
            )

    else:
        logger.info(f"Processing product delete: ID={product_id}")
        handle_product_delete(product)
        try:
            es_service.delete_product(product_id)
            logger.info("Product deleted from ES", extra={"product_id": product_id})
        except Exception as e:
            logger.error(
                "Elasticsearch delete failed",
                extra={"error": str(e), "product_id": product_id},
            )

    remaining = get_all_products()
    logger.info("Products remaining in store", extra={"count": len(remaining)})

    return {"status": "success", "product_id": product_id}
