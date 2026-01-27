"""
Unified Elasticsearch Service for product indexing.
Supports both Shopify and WooCommerce integrations with a common mapping.
"""

from typing import Any, Dict, Optional, List
import traceback
from elasticsearch import Elasticsearch, helpers
from base.models import ProductDocument
from utils.logging import get_logger
import os

logger = get_logger(__name__)

# Unified Index Mapping
PRODUCT_MAPPING = {
    "mappings": {
        "properties": {
            "product_id": {"type": "keyword"},
            "name": {
                "type": "text",
                "fields": {
                    "keyword": {"type": "keyword", "ignore_above": 256}
                }
            },
            "description": {"type": "text"},
            "vendor": {"type": "keyword"},
            "brand": {"type": "keyword"},
            "category": {"type": "keyword"},
            "tags": {"type": "keyword"},
            
            # Search/Filter Helpers
            "price_min": {"type": "float"},
            "price_max": {"type": "float"},
            "total_inventory": {"type": "integer"},
            "status": {"type": "keyword"},
            "updated_at": {"type": "date"},
            "created_at": {"type": "date"},
            "image": {"type": "keyword", "index": False},

            # Nested Variants
            "variants": {
                "type": "nested",
                "properties": {
                    "variant_id": {"type": "keyword"},
                    "sku": {"type": "keyword"},
                    "price": {"type": "float"},
                    "compare_at_price": {"type": "float"},
                    "stock": {"type": "integer"},
                    "image": {"type": "keyword", "index": False},
                    "attributes": {
                        "type": "object",
                        "dynamic": True
                    }
                }
            }
        }
    },
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    }
}

class ElasticsearchService:
    def __init__(self):
        url = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
        user = os.getenv("ELASTIC_USER")
        password = os.getenv("ELASTIC_PASS")
        
        try:
            self.client = Elasticsearch(
                url,
                basic_auth=(user, password) if user and password else None,
                verify_certs=False
            )
            self.index_name = os.getenv("ES_INDEX_NAME", "products_unified")
            if not self.client.ping():
                logger.error(f"Could not connect to Elasticsearch at {url}")
        except Exception as e:
            logger.error(f"Elasticsearch initialization error: {e}")

    def ensure_index_exists(self) -> bool:
        try:
            if not self.client.indices.exists(index=self.index_name):
                logger.info(f"Creating index {self.index_name} with unified mappings")
                self.client.indices.create(
                    index=self.index_name,
                    mappings=PRODUCT_MAPPING["mappings"],
                    settings=PRODUCT_MAPPING["settings"]
                )
            return True
        except Exception as e:
            logger.error(f"Failed to ensure index exists: {e}")
            return False

    def index_product(self, product: ProductDocument) -> bool:
        try:
            self.ensure_index_exists()
            doc = product.dict()
            self.client.index(
                index=self.index_name,
                id=str(product.product_id),
                document=doc
            )
            return True
        except Exception as e:
            logger.error(f"Failed to index product {product.product_id}: {e}")
            return False

    def bulk_index_products(self, products: List[ProductDocument]) -> bool:
        if not products:
            return True
        try:
            self.ensure_index_exists()
            actions = [
                {
                    "_index": self.index_name,
                    "_id": str(p.product_id),
                    "_source": p.dict()
                }
                for p in products
            ]
            success_count, errors = helpers.bulk(self.client, actions)
            if errors:
                logger.error(f"Bulk indexing encountered {len(errors)} errors")
            return success_count > 0
        except Exception as e:
            logger.error(f"Critical failure during bulk indexing: {e}")
            return False

    def delete_product(self, product_id: Any) -> bool:
        try:
            self.client.delete(index=self.index_name, id=str(product_id))
            return True
        except Exception as e:
            logger.error(f"Failed to delete product {product_id}: {e}")
            return False

# Global instance
es_service = ElasticsearchService()
