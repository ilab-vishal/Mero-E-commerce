import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

from shopify.routers import integration as shopify_router
from shopify.webhook import router as shopify_webhook_router
from woocommerce.routers import connection as woo_connection_router
from woocommerce.routers import bulk_sync as woo_sync_router
from woocommerce.webhook import router as woo_webhook_router

from base.elasticsearch_service import es_service
from utils.logging import setup_logging

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Mero E-commerce Integration Platform",
    description="Unified integration platform for Shopify and WooCommerce",
    version="1.0.0",
)

# Register Shopify routers
app.include_router(shopify_webhook_router, tags=["Shopify Webhooks"])
app.include_router(shopify_router.router, prefix="/api/shopify", tags=["Shopify"])

# Register WooCommerce routers
app.include_router(woo_connection_router.router)
app.include_router(woo_sync_router.router)
app.include_router(woo_webhook_router.router)

# Mount static files (Frontend)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
async def startup_event():
    """
    Perform application startup tasks.
    Ensures Elasticsearch index exists.
    """
    # Ensure Elasticsearch index exists
    success = es_service.ensure_index_exists()
    if success:
        logger.info("Elasticsearch index verified/created.")
    else:
        logger.error("Failed to verify/create Elasticsearch index.")


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "platform": "unified"}


@app.get("/", tags=["Root"])
def root():
    return {
        "name": "Mero E-commerce Integration Platform",
        "version": "1.0.0",
        "platforms": ["shopify", "woocommerce"],
        "endpoints": {
            "shopify": "/api/shopify",
            "woocommerce": "/api/woocommerce",
            "health": "/health",
            "docs": "/docs",
        }
    }
