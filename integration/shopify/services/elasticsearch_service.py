"""
Elasticsearch Service for product indexing.

Handles interactions with Elasticsearch for storing, updating,
and deleting product data.
"""

from utils.logging import get_logger
import traceback
from typing import Any, Dict, Optional, List

from elasticsearch import Elasticsearch, helpers

from shopify import config
from shopify.models.product import ProductDocument

logger = get_logger(__name__)

# Index Mapping for Production-Ready Search
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
            
            # Search/Filter Helpers (Top Level)
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
    """
    Service class for interacting with Elasticsearch.
    """

    def __init__(self):
        """
        Initialize the Elasticsearch client.
        """
        try:
            # Connect with basic authentication if credentials are provided
            self.client = Elasticsearch(
                config.ELASTICSEARCH_URL,
                basic_auth=(
                    (config.ELASTIC_USER, config.ELASTIC_PASS)
                    if config.ELASTIC_USER and config.ELASTIC_PASS
                    else None
                ),
                verify_certs=False  # Typically false for local setup
            )
            self.index_name = config.ES_INDEX_NAME
            if not self.client.ping():
                logger.error(
                    "Could not connect to Elasticsearch at %s",
                    config.ELASTICSEARCH_URL
                )
        except Exception as e:
            logger.error("Elasticsearch initialization error: %s", e)

    def ensure_index_exists(self) -> bool:
        """
        Verify the index exists, creating it with mappings if necessary.

        Returns:
            bool: True if index exists or was created, False otherwise.
        """
        try:
            if not self.client.indices.exists(index=self.index_name):
                logger.info(
                    "Creating index %s with explicit mappings",
                    self.index_name
                )
                self.client.indices.create(
                    index=self.index_name,
                    mappings=PRODUCT_MAPPING["mappings"],
                    settings=PRODUCT_MAPPING["settings"]
                )
                return True
            return True
        except Exception as e:
            logger.error("Failed to ensure index exists: %s", e)
            logger.error(traceback.format_exc())
            if hasattr(e, 'body'):
                logger.error("Error body: %s", e.body)
            return False

    def index_product(self, product: ProductDocument) -> bool:
        """
        Index a single product document into Elasticsearch.

        Args:
            product: The product document to index.

        Returns:
            bool: True if indexing was successful.
        """
        try:
            self.ensure_index_exists()
            doc = product.dict()
            response = self.client.index(
                index=self.index_name,
                id=str(product.product_id),
                document=doc
            )
            logger.info(
                "Indexed product %s. Result: %s",
                product.product_id,
                response['result']
            )
            return True
        except Exception as e:
            logger.error(
                "Failed to index product %s: %s",
                product.product_id,
                e
            )
            return False

    def bulk_index_products(self, products: List[ProductDocument]) -> bool:
        """
        Batch index products using the optimized Bulk API.
        
        This is the production-ready approach for handling large catalogs.

        Args:
            products: List of product documents to index.

        Returns:
            bool: True if indexing was successful.
        """
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
                # Sample the first error for debugging
                logger.error(f"Sample error: {errors[0]}")
                
            logger.info(
                f"Successfully bulk indexed {success_count} products "
                f"to {self.index_name}"
            )
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Critical failure during bulk indexing: {e}")
            return False

    def delete_product(self, product_id: int) -> bool:
        """
        Delete a product document from Elasticsearch.

        Args:
            product_id: The ID of the product to delete.

        Returns:
            bool: True if deletion was successful.
        """
        try:
            response = self.client.delete(
                index=self.index_name,
                id=str(product_id)
            )
            logger.info(
                f"Deleted product {product_id} from Elasticsearch. "
                f"Result: {response['result']}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete product {product_id}: {e}")
            return False


# Initialize a global instance
es_service = ElasticsearchService()
