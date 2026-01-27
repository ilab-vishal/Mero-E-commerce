import sys
import os


import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from shopify.webhook import shopify
from woocommerce.webhook import woocommerce
from woocommerce.routers.connection import router as connection_router
from woocommerce.routers.bulk_sync import router as bulk_sync_router
from woocommerce.loggers import setup_logging
from woocommerce.services.elasticsearch_service import es_service
from config import APP_HOST, APP_PORT

# Initialize logging
setup_logging()

# Add the project root to sys.path using an absolute path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

app = FastAPI(title="Ecommerce Webhook Handler")

app.include_router(shopify.router)
app.include_router(woocommerce.router)
app.include_router(connection_router)
app.include_router(bulk_sync_router)


@app.get("/", include_in_schema=False)
async def root():
    es_status = "Connected" if es_service.check_connection() else "Disconnected"
    return {
        "status": "Ecommerce Webhook Handler Running",
        "elasticsearch": es_status
    }


@app.get("/health")
async def health_check():
    """Endpoint for Docker health checks."""
    es_ok = es_service.check_connection()
    return {
        "status": "healthy" if es_ok else "degraded",
        "service": "up",
        "elasticsearch": "up" if es_ok else "down"
    }


if __name__ == "__main__":
    uvicorn.run(app, host=APP_HOST, port=APP_PORT)
