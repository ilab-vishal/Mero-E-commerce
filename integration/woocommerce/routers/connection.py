from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from woocommerce.services.woocommerce_services import test_connection, get_store_product_status_breakdown

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
        # Fetch product breakdown by status
        breakdown = get_store_product_status_breakdown(
            store_url=request.store_url,
            consumer_key=request.consumer_key,
            consumer_secret=request.consumer_secret
        )
        
        total = breakdown.get("total", 0)
        
        # Build status breakdown message
        status_parts = []
        for status in ["publish", "draft", "pending", "private"]:
            if status in breakdown and breakdown[status] > 0:
                status_parts.append(f"{breakdown[status]} {status}")
        
        status_message = ", ".join(status_parts) if status_parts else "0"
        
        return {
            "status": "success",
            "message": "Successfully connected to WooCommerce!", 
            "details": f"Success! We found {total} product{'s' if total != 1 else ''} in your store ({status_message}). You are ready to start synchronization.",
            "total_store_products": total,
            "product_breakdown": breakdown
        }
    else:
        raise HTTPException(status_code=400, detail=result.get("message", "Connection failed"))
