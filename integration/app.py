import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from base.elasticsearch_service import es_service
from config import APP_NAME, APP_HOST, APP_PORT, DEBUG
from shopify.routers import integration as shopify_router
from shopify.webhook import router as shopify_webhook_router
from utils.logging import setup_logging
from woocommerce.routers import bulk_sync as woo_sync_router
from woocommerce.routers import connection as woo_connection_router
from woocommerce.webhook.woocommerce import router as woo_webhook_router

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

from fastapi.middleware.cors import CORSMiddleware

# Create FastAPI application
app = FastAPI(
    title="Mero E-commerce Integration Platform",
    description="Unified integration platform for Shopify and WooCommerce",
    version="1.0.0",
)

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Shopify routers
app.include_router(shopify_webhook_router, tags=["Shopify Webhooks"])
app.include_router(shopify_router.router, tags=["Shopify"])

# Register WooCommerce routers
app.include_router(woo_connection_router.router)
app.include_router(woo_sync_router.router)
app.include_router(woo_webhook_router)

# Register Chatbot router
from chatbot.router import router as chatbot_router
app.include_router(chatbot_router)

@app.on_event("startup")
async def startup_event():
    """
    Perform application startup tasks.
    Ensures Elasticsearch index exists.
    """
    # Ensure Elasticsearch index exists
    success = es_service.ensure_index_exists()
    success_enhanced = es_service.ensure_enhanced_index_exists()
    
    if success and success_enhanced:
        logger.info("Elasticsearch indices verified/created.")
    else:
        logger.error("Failed to verify/create Elasticsearch indices.")


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "platform": "unified"}


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Mero E-commerce Integration API",
        "status": "online",
        "docs": "/docs"
    }
