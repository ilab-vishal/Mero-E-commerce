# E-Commerce Integration Platform

A modular, extensible platform for integrating multiple e-commerce platforms (Shopify, WooCommerce, Magento, etc.) with a unified API interface and webhook handling system.

## 🏗️ Architecture Overview

This project follows a **plugin-based architecture** where each e-commerce platform is implemented as a separate integration module that extends a common base interface.

```
Integration/
├── base/                          # Core abstract classes
│   ├── base.py                   # CatalogBase - Abstract base class
│   └── integrations.py           # Enum of supported integrations
├── shopify/                       # Shopify integration module
│   ├── config.py                 # Shopify-specific configuration
│   ├── connection_adapter/       # API client implementation
│   │   └── adapter.py           # ShopifyEngine class
│   ├── services/                 # Business logic and API calls
│   │   └── shopify_services.py  # Authentication and data fetching
│   ├── routers/                  # Webhook route handlers
│   │   ├── product_create.py
│   │   ├── product_update.py
│   │   └── product_delete.py
│   ├── utils/                    # Webhook utilities
│   │   └── shopify_router_utils.py
│   └── webhook/                  # Webhook router configuration
│       └── shopify.py
├── utils/                         # Shared utilities
│   └── response_formatter.py     # Data formatting utilities
├── config.py                      # App-level configuration (host/port)
├── app.py                         # FastAPI webhook server
├── main.py                        # Example usage
└── __init__.py                    # Factory pattern for engine creation
```

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- pip or uv package manager

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd Integration

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file for local development.

App-level settings:

```bash
APP_HOST=127.0.0.1
APP_PORT=8050
```

Shopify integration settings (used by `shopify/config.py`):

```bash
SHOPIFY_STORE_URL=showcasevault.myshopify.com
SHOPIFY_CLIENT_ID=your_client_id
SHOPIFY_CLIENT_SECRET=your_client_secret
SHOPIFY_WEBHOOK_SECRET=your_webhook_secret
SHOPIFY_API_VERSION=2026-01
SHOPIFY_DEFAULT_CLIENT_KEY=12345
```

### Usage

#### Fetching Products

```python
from shopify.connection_adapter.adapter import ShopifyEngine
from utils.response_formatter import format_single_product_data

# Initialize engine
shopify_engine = ShopifyEngine("client_id")

# Get single product
product = shopify_engine.get_product(product_id=7530792648779)
format_single_product_data(product)

# List all products
products = shopify_engine.list_products(limit=10)
```

#### Running Webhook Server

```bash
# Start the webhook server
python app.py

# Or with uvicorn
uvicorn app:app --host 127.0.0.1 --port 8050
```

The webhook endpoints will be available at:
- `POST /webhooks/shopify/products/create`
- `POST /webhooks/shopify/products/update`
- `POST /webhooks/shopify/products/delete`

## 📚 Adding a New Integration (WooCommerce, Magento, etc.)

Follow these steps to add support for a new e-commerce platform:

### Step 1: Update Integration Enum

Add your integration to `base/integrations.py`:

```python
from enum import Enum

class Integrations(Enum):
    SHOPIFY = "shopify"
    WOOCOMMERCE = "woocommerce"  # Add new integration
    MAGENTO = "magento"          # Add new integration
```

### Step 2: Create Integration Module Structure

Create a new directory for your integration:

```bash
mkdir -p <platform_name>/connection_adapter
mkdir -p <platform_name>/routers
mkdir -p <platform_name>/utils
mkdir -p <platform_name>/webhook
```

Example for WooCommerce:
```
woocommerce/
├── connection_adapter/
│   └── adapter.py           # WooCommerceEngine class
├── routers/
│   ├── product_create.py
│   ├── product_update.py
│   └── product_delete.py
├── utils/
│   ├── woocommerce_utils.py
│   └── woocommerce_router_utils.py
└── webhook/
    └── woocommerce.py
```

### Step 3: Implement the Adapter Class

Create `<platform_name>/connection_adapter/adapter.py` that extends `CatalogBase`:

```python
from base.base import CatalogBase
from <platform_name>.utils.<platform_name>_utils import get_access_token, list_client_products, get_product

class WooCommerceEngine(CatalogBase):
    def __init__(self, client_id: str):
        self._access_token = None
        super().__init__(client_id)
    
    def _get_access_token(self):
        """Implement authentication logic"""
        if self._access_token is None:
            # Your authentication implementation
            pass
    
    def list_products(self, limit: int = None):
        """Implement product listing"""
        self._get_access_token()
        # Your implementation
        pass
    
    def get_product(self, product_id: int):
        """Implement single product fetch"""
        self._get_access_token()
        # Your implementation
        pass
```

**Required Methods:**
- `list_products(limit: int = None)` - Fetch multiple products
- `get_product(product_id: int)` - Fetch a single product by ID

### Step 4: Implement Utility Functions

Create `<platform_name>/utils/<platform_name>_utils.py`:

```python
import requests

_store_url = {
    "client_id_1": "your-store-url.com"
}

_client_secrets = {
    "client_id_1": {
        "client_key": "your_key",
        "client_secret": "your_secret"
    }
}

def _get_store_url(client_id: str):
    return _store_url.get(client_id)

def get_access_token(client_id: str):
    """Implement OAuth or API key authentication"""
    # Return: {"access_token": "...", "expires_in": 3600}
    pass

def list_client_products(client_id: str, access_token: str, limit: int = None):
    """Fetch products from the platform API"""
    # Return: JSON response with products
    pass

def get_product(client_id: str, access_token: str, product_id: int):
    """Fetch single product from the platform API"""
    # Return: JSON response with product data
    pass
```

### Step 5: Implement Webhook Handlers

Create webhook route handlers in `<platform_name>/routers/`:

**`product_create.py`:**
```python
from fastapi import APIRouter, Request, Header, HTTPException
import json
from <platform_name>.utils.<platform_name>_router_utils import verify_webhook, is_duplicate_event

router = APIRouter()

@router.post("/products/create")
async def product_created(
    request: Request,
    x_webhook_signature: str = Header(None),
    x_event_id: str = Header(None)
):
    # 1. Check for duplicate events
    if x_event_id and is_duplicate_event(x_event_id):
        return 200
    
    # 2. Verify webhook signature
    body = await request.body()
    if not verify_webhook(body, x_webhook_signature):
        raise HTTPException(status_code=401, detail="Invalid webhook")
    
    # 3. Process webhook data
    product = json.loads(body.decode("utf-8"))
    
    # Your business logic here
    print(f"Product created: {product.get('id')}")
    
    return 200
```

Create similar files for `product_update.py` and `product_delete.py`.

### Step 6: Create Webhook Router Utils

Create `<platform_name>/utils/<platform_name>_router_utils.py`:

```python
import hmac
import hashlib
import base64
from datetime import datetime, timedelta
from config import <PLATFORM>_WEBHOOK_SECRET

processed_event_ids = {}

def is_duplicate_event(event_id: str) -> bool:
    """Prevent duplicate webhook processing"""
    current_time = datetime.now()
    
    if event_id in processed_event_ids:
        return True
    
    processed_event_ids[event_id] = current_time
    
    # Cleanup old events (older than 24 hours)
    for eid in list(processed_event_ids.keys()):
        if (current_time - processed_event_ids[eid]) > timedelta(hours=24):
            del processed_event_ids[eid]
    
    return False

def verify_webhook(data: bytes, signature: str) -> bool:
    """Verify webhook signature based on platform's method"""
    # Implement platform-specific signature verification
    # Example for HMAC-SHA256:
    digest = hmac.new(
        <PLATFORM>_WEBHOOK_SECRET.encode("utf-8"),
        data,
        hashlib.sha256
    ).digest()
    
    computed_signature = base64.b64encode(digest).decode("utf-8")
    return hmac.compare_digest(computed_signature, signature)
```

### Step 7: Configure Webhook Router

Create `<platform_name>/webhook/<platform_name>.py`:

```python
from fastapi import APIRouter

from <platform_name>.routers.product_create import router as create_router
from <platform_name>.routers.product_update import router as update_router
from <platform_name>.routers.product_delete import router as delete_router

router = APIRouter(prefix="/webhooks/<platform_name>", tags=["<PlatformName>"])

router.include_router(create_router)
router.include_router(update_router)
router.include_router(delete_router)
```

### Step 8: Register in Main App

Update `app.py` to include your webhook router:

```python
import uvicorn
from fastapi import FastAPI

from shopify.webhook import shopify
from woocommerce.webhook import woocommerce  # Add import

app = FastAPI(title="E-Commerce Webhook Handler")

app.include_router(shopify.router)
app.include_router(woocommerce.router)  # Add router

@app.get("/", include_in_schema=False)
async def root():
    return {"status": "Webhook Handler Running"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8050)
```

### Step 9: Update Factory Pattern

Update `__init__.py` to support your new integration:

```python
from base.integrations import Integrations
from shopify.connection_adapter.adapter import ShopifyEngine
from woocommerce.connection_adapter.adapter import WooCommerceEngine  # Add import

__all__ = ["ShopifyEngine", "WooCommerceEngine", "Integrations"]

def get_engine(integration_name: str, client_id: str):
    if integration_name == Integrations.SHOPIFY.value:
        return ShopifyEngine(client_id)
    elif integration_name == Integrations.WOOCOMMERCE.value:
        return WooCommerceEngine(client_id)  # Add case
    else:
        raise ValueError(f"Unknown integration: {integration_name}")
```

### Step 10: Add Configuration

Update `config.py` with platform-specific settings:

```python
# WooCommerce Configuration
WOOCOMMERCE_CONSUMER_KEY = "your_consumer_key"
WOOCOMMERCE_CONSUMER_SECRET = "your_consumer_secret"
WOOCOMMERCE_WEBHOOK_SECRET = "your_webhook_secret"

def get_woocommerce_products_url(store_url: str):
    return f"https://{store_url}/wp-json/wc/v3/products"

def get_woocommerce_product_url(store_url: str, product_id: int):
    return f"https://{store_url}/wp-json/wc/v3/products/{product_id}"
```

## 🔧 Platform-Specific Implementation Notes

### WooCommerce
- **Authentication**: Uses Consumer Key/Secret (Basic Auth or OAuth)
- **API Endpoint**: `/wp-json/wc/v3/`
- **Webhook Signature**: HMAC-SHA256 in `X-WC-Webhook-Signature` header
- **Event ID**: Use `X-WC-Webhook-ID` header

### Magento
- **Authentication**: Token-based authentication
- **API Endpoint**: `/rest/V1/`
- **Webhook**: Custom implementation or use Magento webhooks module
- **Event Tracking**: Implement custom event ID tracking

### BigCommerce
- **Authentication**: OAuth 2.0
- **API Endpoint**: `/stores/{store_hash}/v3/`
- **Webhook Signature**: Digital signature verification
- **Event ID**: Use webhook event ID from payload

## 📝 Code Standards

### Naming Conventions
- **Module names**: lowercase with underscores (`woocommerce`, `magento`)
- **Class names**: PascalCase (`WooCommerceEngine`, `MagentoEngine`)
- **Function names**: lowercase with underscores (`get_product`, `list_products`)

### Required Implementations
Every integration MUST implement:
1. `CatalogBase` abstract class methods
2. Webhook handlers for create, update, delete events
3. HMAC/signature verification for webhooks
4. Duplicate event detection
5. Error handling and logging

### Testing
Add tests for your integration:
```python
# tests/test_woocommerce.py
def test_woocommerce_list_products():
    engine = WooCommerceEngine("test_client_id")
    products = engine.list_products(limit=5)
    assert products is not None
```

## 🔒 Security Best Practices

1. **Never commit credentials** - Use environment variables or `.env` files
2. **Verify webhook signatures** - Always validate incoming webhooks
3. **Implement rate limiting** - Protect against abuse
4. **Use HTTPS** - Always use secure connections
5. **Sanitize inputs** - Validate and sanitize all user inputs

## 📖 API Documentation

Once the server is running, access the auto-generated API documentation:
- **Swagger UI**: http://127.0.0.1:8050/docs
- **ReDoc**: http://127.0.0.1:8050/redoc

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/magento-integration`)
3. Follow the integration guide above
4. Write tests for your integration
5. Commit your changes (`git commit -m 'Add Magento integration'`)
6. Push to the branch (`git push origin feature/magento-integration`)
7. Open a Pull Request

### Pull Request Checklist
- [ ] Code follows the project structure
- [ ] All required methods are implemented
- [ ] Webhook handlers include signature verification
- [ ] Duplicate event detection is implemented
- [ ] Configuration is added to `config.py`
- [ ] Integration is registered in `__init__.py`
- [ ] Tests are added (if applicable)
- [ ] Documentation is updated

## 📄 License

[Add your license here]

## 🆘 Support

For issues, questions, or contributions, please open an issue on GitHub.

## 🗺️ Roadmap

- [x] Shopify integration
- [ ] WooCommerce integration
- [ ] Magento integration
- [ ] BigCommerce integration
- [ ] Inventory sync functionality
- [ ] Order management
- [ ] Customer data sync
- [ ] Analytics and reporting

## 📚 Additional Resources

- [Shopify API Documentation](https://shopify.dev/docs/api)
- [WooCommerce REST API](https://woocommerce.github.io/woocommerce-rest-api-docs/)
- [Magento REST API](https://devdocs.magento.com/guides/v2.4/rest/bk-rest.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
