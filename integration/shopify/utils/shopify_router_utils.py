"""
Shopify webhook router utilities.

Contains helper functions for webhook verification and duplicate event detection.
"""

import hmac
import hashlib
import base64
import logging
from datetime import datetime, timedelta
from typing import Dict

from config import SHOPIFY_WEBHOOK_SECRET

logger = logging.getLogger(__name__)

# In-memory store for processed event IDs (for duplicate detection)
_processed_event_ids: Dict[str, datetime] = {}


def is_duplicate_event(event_id: str) -> bool:
    """
    Check if a webhook event has already been processed.
    
    Shopify may send the same webhook multiple times. This function
    checks (but does NOT mark) if an event was already processed.
    """
    if event_id in _processed_event_ids:
        logger.debug(f"Duplicate event detected: {event_id}")
        return True
    return False


def mark_event_processed(event_id: str) -> None:
    """
    Mark an event as successfully processed.
    """
    current_time = datetime.now()
    _processed_event_ids[event_id] = current_time
    
    # Cleanup old events (older than 24 hours)
    cleanup_threshold = current_time - timedelta(hours=24)
    expired_ids = [
        eid for eid, timestamp in _processed_event_ids.items()
        if timestamp < cleanup_threshold
    ]
    for eid in expired_ids:
        del _processed_event_ids[eid]


def verify_shopify_webhook(data: bytes, hmac_header: str) -> bool:
    """
    Verify that a webhook request is genuinely from Shopify.
    """
    if not SHOPIFY_WEBHOOK_SECRET:
        logger.error("SHOPIFY_WEBHOOK_SECRET is not configured!")
        return False
    
    if not hmac_header:
        logger.warning("Missing HMAC header in webhook request")
        return False
    
    # Compute the expected HMAC
    digest = hmac.new(
        SHOPIFY_WEBHOOK_SECRET.encode("utf-8"),
        data,
        hashlib.sha256
    ).digest()
    
    computed_hmac = base64.b64encode(digest).decode("utf-8")
    is_valid = hmac.compare_digest(computed_hmac, hmac_header)
    
    return is_valid
