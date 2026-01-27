"""
Utilities for automatic Shopify webhook registration.
"""

from utils.logging import get_logger
from typing import List

from shopify.config import SHOPIFY_STORE_URL, SHOPIFY_ACCESS_TOKEN, NGROK_URL
from shopify.services.shopify_services import register_client_webhook

logger = get_logger(__name__)

TOPICS = [
    "products/create",
    "products/update",
    "products/delete"
]


def auto_register_webhooks():
    """
    Automatically register standard product webhooks on application startup.
    Uses the NGROK_URL configured in the environment.
    """
    if not SHOPIFY_STORE_URL or not SHOPIFY_ACCESS_TOKEN:
        logger.warning(
            "Skipping auto-registration: Shopify credentials not fully configured."
        )
        return

    if not NGROK_URL:
        logger.warning(
            "Skipping auto-registration: NGROK_URL not found in environment."
        )
        return

    logger.info(
        f"Auto-registering webhooks for {SHOPIFY_STORE_URL} using {NGROK_URL}"
    )

    for topic in TOPICS:
        address = f"{NGROK_URL}/webhooks/shopify/{topic}"
        try:
            result = register_client_webhook(
                store_url=SHOPIFY_STORE_URL,
                access_token=SHOPIFY_ACCESS_TOKEN,
                topic=topic,
                address=address
            )
            
            # Handle results
            errors = result.get("errors", {})
            if not errors:
                logger.info(f"✅ Webhook for {topic} registered successfully.")
            elif "address" in errors and any(
                "already been taken" in str(e) for e in errors["address"]
            ):
                logger.info(f"✅ Webhook for {topic} is already active.")
            else:
                logger.error(f"❌ Failed to auto-register {topic}: {result}")
                
        except Exception as e:
            logger.error(f"Exception during auto-registration of {topic}: {e}")
