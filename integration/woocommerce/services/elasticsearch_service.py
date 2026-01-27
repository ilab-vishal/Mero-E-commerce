# ============================================================
# ELASTICSEARCH SERVICE
# Handles indexing, deleting, and searching products in ES
# ============================================================

import logging
from elasticsearch import Elasticsearch, exceptions
from elasticsearch.helpers import bulk
from woocommerce.config import (
    ELASTICSEARCH_URL, 
    ELASTICSEARCH_INDEX_NAME,
    ELASTIC_USER,
    ELASTIC_PASS
)
from woocommerce.utils.product_transformer import transform_product_for_es

logger = logging.getLogger(__name__)


class ElasticsearchService:
    def __init__(self):
        self.es = Elasticsearch(
            ELASTICSEARCH_URL,
            basic_auth=(ELASTIC_USER, ELASTIC_PASS),
            verify_certs=False,
            request_timeout=5,
            max_retries=3,
            retry_on_timeout=True,
        )
        self.index_name = ELASTICSEARCH_INDEX_NAME
        self._initialized = False

    def check_connection(self):
        """Check if Elasticsearch is reachable."""
        try:
            return self.es.ping()
        except Exception:
            return False

    def initialize(self):
        """Lazy initialization of indices."""
        if self._initialized:
            return True
        
        try:
            if self.check_connection():
                self.ensure_index_exists()
                self._initialized = True
                logger.info("Elasticsearch initialization successful")
                return True
            else:
                logger.warning("Elasticsearch connection failed during initialization")
                return False
        except Exception as e:
            logger.error(f"Error during ES initialization: {e}")
            return False

    def ensure_index_exists(self):
        """Create index with mapping if it doesn't exist."""
        mapping = {
            "mappings": {
                "properties": {
                    "product_id": {"type": "keyword"},
                    "name": {"type": "text", "fields": {"raw": {"type": "keyword"}}},
                    "description": {"type": "text"},
                    "short_description": {"type": "text"},
                    "categories": {"type": "keyword"},
                    "tags": {"type": "keyword"},
                    "brands": {"type": "keyword"},
                    "images": {"type": "keyword"},
                    "attributes": {"type": "object"},
                    "variants": {
                        "type": "nested",
                        "properties": {
                            "variant_id": {"type": "keyword"},
                            "attributes": {"type": "object"},
                            "price": {"type": "double"},
                            "regular_price": {"type": "double"},
                            "sale_price": {"type": "double"},
                            "stock_quantity": {"type": "integer"},
                            "stock_status": {"type": "keyword"},
                        },
                    },
                }
            }
        }

        try:
            if not self.es.indices.exists(index=self.index_name):
                self.es.indices.create(index=self.index_name, body=mapping)
                logger.info(f"Elasticsearch index '{self.index_name}' created")
            else:
                logger.info(f"Elasticsearch index '{self.index_name}' already exists")
        except Exception as e:
            logger.error(f"Failed to verify/create ES index: {e}")
            raise

    def index_product(self, product):
        """Index (create or update) a product in Elasticsearch."""
        if not self.initialize():
            logger.error("Cannot index product: Elasticsearch not initialized")
            return False

        try:
            doc = transform_product_for_es(product)
            logger.debug(f"Indexing document: {doc.get('product_id')}")
            self.es.index(index=self.index_name, id=doc["product_id"], document=doc)
            logger.info(f"Product {doc['product_id']} successfully indexed in ES")
            return True
        except Exception as e:
            logger.error(f"ES indexing failed for product {product.get('id', 'unknown')}: {e}")
            return False

    def delete_product(self, product_id):
        """Delete a product from Elasticsearch."""
        if not self.initialize():
            return False

        try:
            self.es.delete(index=self.index_name, id=str(product_id))
            logger.info(f"Product {product_id} deleted from ES")
            return True
        except exceptions.NotFoundError:
            return False
        except Exception as e:
            logger.error(f"ES delete failed: {e}")
            return False

    def search_products(self, query_string=None, filters=None):
        """Search products in Elasticsearch."""
        if not self.initialize():
            return []

        query = {"bool": {"must": [], "filter": []}}

        if query_string:
            query["bool"]["must"].append({
                "multi_match": {
                    "query": query_string,
                    "fields": ["name^2", "description", "attributes.*"],
                }
            })
        else:
            query["bool"]["must"].append({"match_all": {}})

        if filters:
            for key, value in filters.items():
                query["bool"]["filter"].append({"term": {key: value}})

        try:
            response = self.es.search(index=self.index_name, query=query)
            return response["hits"]["hits"]
        except Exception as e:
            logger.error(f"ES search failed: {e}")
            return []

    def bulk_index_products(self, products: list) -> dict:
        """
        Bulk index multiple products into Elasticsearch.
        Returns a dict with success_count, failed_count, and failures list.
        """
        if not self.initialize():
            logger.error("Cannot bulk index: Elasticsearch not initialized")
            return {"success_count": 0, "failed_count": len(products), "failures": []}

        if not products:
            return {"success_count": 0, "failed_count": 0, "failures": []}

        actions = []
        transform_failures = []

        for product in products:
            try:
                doc = transform_product_for_es(product)
                if doc and doc.get("product_id"):
                    actions.append({
                        "_index": self.index_name,
                        "_id": doc["product_id"],
                        "_source": doc
                    })
                else:
                    transform_failures.append({
                        "product_id": product.get("id", "unknown"),
                        "error": "Transform returned empty document"
                    })
            except Exception as e:
                transform_failures.append({
                    "product_id": product.get("id", "unknown"),
                    "error": str(e)
                })

        if not actions:
            return {
                "success_count": 0,
                "failed_count": len(transform_failures),
                "failures": transform_failures
            }

        try:
            success_count, errors = bulk(
                self.es,
                actions,
                raise_on_error=False,
                raise_on_exception=False
            )

            # Process bulk errors
            bulk_failures = []
            if errors:
                for error in errors:
                    bulk_failures.append({
                        "product_id": error.get("index", {}).get("_id", "unknown"),
                        "error": str(error.get("index", {}).get("error", "Unknown error"))
                    })

            all_failures = transform_failures + bulk_failures
            failed_count = len(all_failures)

            logger.info(f"Bulk indexing complete: {success_count} succeeded, {failed_count} failed")
            return {
                "success_count": success_count,
                "failed_count": failed_count,
                "failures": all_failures
            }

        except Exception as e:
            logger.error(f"Bulk indexing failed: {e}")
            return {
                "success_count": 0,
                "failed_count": len(products),
                "failures": [{"product_id": "bulk_operation", "error": str(e)}]
            }


# Singleton instance
es_service = ElasticsearchService()
