from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from woocommerce.services.woocommerce_services import test_connection, get_store_product_count

router = APIRouter(prefix="/api/woocommerce", tags=["WooCommerce Connection"])

class ConnectionRequest(BaseModel):
    store_url: str | None = None
    consumer_key: str | None = None
    consumer_secret: str | None = None

@router.post("/connect")
async def connect_woocommerce(request: ConnectionRequest):
    """
    Test the connection to WooCommerce using provided credentials.
    """
    result = test_connection(
        store_url=request.store_url,
        consumer_key=request.consumer_key,
        consumer_secret=request.consumer_secret
    )
    
    if result["status"] == "success":
        # Also fetch total product count for the frontend
        total_count = get_store_product_count(
            store_url=request.store_url,
            consumer_key=request.consumer_key,
            consumer_secret=request.consumer_secret
        )
        return {
            "status": "success",
            "message": "Successfully connected to WooCommerce!", 
            "details": f"Success! We found {total_count} products in your store. You are ready to start synchronization.",
            "total_store_products": total_count
        }
    else:
        raise HTTPException(status_code=400, detail=result.get("message", "Connection failed"))
