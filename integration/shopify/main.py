import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from shopify.routers import integration
from shopify.services.elasticsearch_service import es_service
from shopify.utils.webhook_utils import auto_register_webhooks
from shopify.webhook import router as shopify_webhook_router
from utils.logging import setup_logging

# Initialize logging
setup_logging()

# Create FastAPI application
app = FastAPI(
    title="Shopify Sales Agent Integration",
    description="Modular e-commerce integration platform",
    version="1.0.0",
)

# Register routers
app.include_router(shopify_webhook_router)
app.include_router(integration.router)

# Mount static files (Frontend)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
async def startup_event():
    """
    Perform application startup tasks.
    Ensures Elasticsearch index exists and auto-registers webhooks with Shopify.
    """
    # Ensure Elasticsearch index exists
    es_service.ensure_index_exists()
    
    # Auto-register webhooks with Shopify
    try:
        auto_register_webhooks()
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to auto-register webhooks: {e}")


@app.get("/health", tags=["Health"])
def health_check():
    """
    Health check endpoint for load balancers and monitoring.
    
    Returns:
        A dictionary indicating the service status.
    """
    return {"status": "ok"}


@app.get("/", tags=["Root"])
def root():
    """
    Root endpoint with API information and available endpoints.
    
    Returns:
        A dictionary containing API name, version, and key endpoint paths.
    """
    return {
        "name": "Shopify Sales Agent Integration",
        "version": "1.0.0",
        "endpoints": {
            "webhooks": "/webhooks/shopify/products/{create|update|delete}",
            "health": "/health",
            "docs": "/docs",
        }
    }
