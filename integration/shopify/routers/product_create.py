from fastapi import APIRouter, Request, Header, HTTPException
import json
from shopify.utils.shopify_router_utils import verify_shopify_webhook, is_duplicate_event

router = APIRouter()

@router.post("/products/create")
async def product_created(
    request: Request,
    x_shopify_hmac_sha256: str = Header(None),
    x_shopify_event_id: str = Header(None)
):
    if x_shopify_event_id and is_duplicate_event(x_shopify_event_id):
        return 200
    
    body = await request.body()

    if not x_shopify_hmac_sha256:
        raise HTTPException(status_code=401)

    if not verify_shopify_webhook(body, x_shopify_hmac_sha256):
        raise HTTPException(status_code=401, detail="Invalid webhook")

    product = json.loads(body.decode("utf-8"))

    # Do something with the product data

    return 200
