import hmac
import hashlib
import base64
import logging
from datetime import datetime, timedelta
from shopify.config import get_shopify_webhook_secret

from api.utils.encryption import decrypt_value


logger = logging.getLogger("integration.shopify.webhook")

processed_event_ids = {}

def is_duplicate_event(event_id: str) -> bool:
    current_time = datetime.now()
    
    if event_id in processed_event_ids:
        return True
    
    processed_event_ids[event_id] = current_time
    
    for eid in list(processed_event_ids.keys()):
        if (current_time - processed_event_ids[eid]) > timedelta(hours=24):
            del processed_event_ids[eid]
    
    return False

async def verify_shopify_webhook(data: bytes, hmac_header: str, client_id: str):
    try:
        secret = await get_shopify_webhook_secret(client_id)
        secret = decrypt_value(secret)
    except Exception:
        logger.exception("Failed to fetch Shopify webhook secret - client_id=%s", client_id)
        return False

    if not secret:
        logger.warning("Missing Shopify webhook secret - client_id=%s", client_id)
        return False

    secret = secret.strip()
    digest = hmac.new(secret.encode("utf-8"), data, hashlib.sha256).digest()
    computed_hmac = base64.b64encode(digest).decode("utf-8")

    if not hmac.compare_digest(computed_hmac, (hmac_header or "").strip()):
        logger.warning("Invalid Shopify webhook signature - client_id=%s", client_id)
        return False

    return True