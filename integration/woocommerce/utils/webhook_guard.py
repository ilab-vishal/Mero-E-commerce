def is_woocommerce_ping(topic: str, body: bytes) -> bool:
    if topic == "action.woocommerce_ping":
        return True

    try:
        text = body.decode("utf-8")
        return text.startswith("webhook_id=")
    except Exception:
        return False
