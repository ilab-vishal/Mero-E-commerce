import base64
import hashlib
import hmac
from datetime import datetime, timedelta

from config import WOOCOMMERCE_WEBHOOK_SECRET


processed_event_ids = {}

def is_duplicate_event(event_id: str, product_id: int = None) -> bool:
    """
    Check if this webhook event is a duplicate.
    Uses composite key of webhook_id + product_id to allow both 
    parent and variation updates from same webhook delivery.
    """
    current_time = datetime.now()
    
    # Create composite key: webhook_id + product_id
    composite_key = f"{event_id}_{product_id}" if product_id else event_id
    
    if composite_key in processed_event_ids:
        return True
    
    processed_event_ids[composite_key] = current_time
    
    # Cleanup old entries (older than 24 hours)
    for eid in list(processed_event_ids.keys()):
        if (current_time - processed_event_ids[eid]) > timedelta(hours=24):
            del processed_event_ids[eid]
    
    return False

def verify_woocommerce_webhook(data: bytes, signature: str) -> bool:
    if not WOOCOMMERCE_WEBHOOK_SECRET:
        return False
    digest = hmac.new(
        WOOCOMMERCE_WEBHOOK_SECRET.encode("utf-8"),
        data,
        hashlib.sha256
    ).digest()

    computed_signature = base64.b64encode(digest).decode("utf-8")
    return hmac.compare_digest(computed_signature, signature)
