import json

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from utils.woocommerce_formatter import format_merged_product
from utils.woocommerce_store import (
    get_product,
    handle_parent_product,
    handle_variant_product,
)
from woocommerce.loggers import get_logger
from base.elasticsearch_service import es_service
from woocommerce.services.woocommerce_services import (
    get_product as fetch_remote_product,
)
from woocommerce.utils.product_transformer import transform_product_for_es
from woocommerce.utils.webhook_guard import is_woocommerce_ping
from woocommerce.utils.woocommerce_router_utils import verify_woocommerce_webhook

router = APIRouter()
logger = get_logger("product_update")


@router.post("/products/update")
async def product_updated(
    request: Request,
    x_wc_webhook_signature: str = Header(None),
    x_wc_webhook_topic: str = Header(None),
):
    logger.info(
        "Received WooCommerce product update webhook",
        extra={"topic": x_wc_webhook_topic},
    )

    body_bytes = await request.body()

    # Ping check
    if is_woocommerce_ping(x_wc_webhook_topic, body_bytes):
        logger.info("Ping received", extra={"topic": x_wc_webhook_topic})
        return {"status": "pong"}

    # Signature verification
    if not x_wc_webhook_signature or not verify_woocommerce_webhook(
        body_bytes, x_wc_webhook_signature
    ):
        logger.warning(
            "Invalid webhook signature", extra={"topic": x_wc_webhook_topic}
        )
        raise HTTPException(status_code=401, detail="Invalid webhook")

    # Parse payload
    product = json.loads(body_bytes.decode("utf-8"))
    product_id = product.get("id")

    # No deduplication: always process and index the update event

    # Process product
    merged = None
    if product.get("type") == "variation":
        logger.info(f"Processing variation update: ID={product_id}")
        # Update the variant in store
        handle_variant_product(product)
        parent_id = product.get("parent_id")

        # Fetch all variants for the parent from WooCommerce and update store
        try:
            parent_product = fetch_remote_product(parent_id)
            if parent_product and "variations" in parent_product:
                for variant_id in parent_product["variations"]:
                    variant_data = fetch_remote_product(variant_id)
                    if variant_data:
                        handle_variant_product(variant_data)
        except Exception as e:
            logger.error(f"Error fetching all variants: {e}", extra={"parent_id": parent_id})

        # Always re-index the parent
        merged = get_product(parent_id)
        if merged:
             logger.info(
                "Parent product ready for re-indexing after variant update",
                extra={"parent_id": parent_id, "variant_id": product_id}
            )
    else:
        logger.info(f"Processing parent product update: ID={product_id}")
        # Update parent product in store
        merged = handle_parent_product(product)
        
        # If variable product, fetch and update all variations
        if product.get("type") == "variable" and "variations" in product:
            logger.info(f"Fetching variations for updated parent product: ID={product_id}")
            try:
                for variant_id in product["variations"]:
                    variant_data = fetch_remote_product(variant_id)
                    if variant_data:
                        handle_variant_product(variant_data)
            except Exception as e:
                logger.error(f"Error fetching variations for parent update: {e}", extra={"product_id": product_id})

        if merged:
            logger.info("Parent product processed", extra={"product_id": product_id})

    if not merged:
        logger.error(
            "No merged product found for update",
            extra={"product_id": product_id}
        )
        return JSONResponse(
            status_code=500, content={"status": "error", "reason": "No merged product"}
        )

    # Index in ES
    try:
        logger.info(f"Indexing updated product: ID={merged.get('id')}")
        product_doc = transform_product_for_es(merged)
        result = es_service.index_product(product_doc)
        if result:
            logger.info("Successfully updated product in ES", extra={"product_id": merged.get('id')})
        else:
             logger.error("ES index returned False", extra={"product_id": merged.get('id')})
             return JSONResponse(
                status_code=500,
                content={"status": "error", "reason": "ES index failed"},
            )
    except Exception as e:
        logger.error(
            "Exception during ES index",
            extra={"error": str(e), "product_id": merged.get('id')}
        )
        return JSONResponse(
            status_code=500, content={"status": "error", "reason": str(e)}
        )

    # Debug output
    format_merged_product(merged)

    return {"status": "success", "product_id": product_id}
