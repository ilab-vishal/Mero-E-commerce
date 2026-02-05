"""
Unified Elasticsearch Service for product indexing.
Supports both Shopify and WooCommerce integrations with a common mapping.
"""

import os
import traceback
from typing import Any, Dict, Optional, List

from elasticsearch import Elasticsearch, helpers

from base.models import ProductDocument
from utils.logging import get_logger

logger = get_logger(__name__)

# Unified Index Mapping
PRODUCT_MAPPING = {
    "mappings": {
        "properties": {
            "product_id": {"type": "keyword"},
            "name": {
                "type": "text",
                "analyzer": "standard",
                "fields": {
                    "keyword": {"type": "keyword", "ignore_above": 256},
                    "autocomplete": {
                        "type": "text",
                        "analyzer": "autocomplete"
                    }
                }
            },
            "description": {"type": "text"},
            "vendor": {"type": "keyword"},
            "brand": {"type": "keyword"},
            "categories": {"type": "keyword"},
            "tags": {"type": "keyword"},
            "slug": {"type": "keyword"},
            
            # Search/Filter Helpers
            "price_min": {"type": "float"},
            "price_max": {"type": "float"},
            "currency": {"type": "keyword"},
            "total_inventory": {"type": "integer"},
            "status": {"type": "keyword"},
            "on_sale": {"type": "boolean"},
            
            # Media
            "primary_image": {"type": "keyword", "index": False},
            "images": {"type": "keyword", "index": False},

            # Nested Variants
            "variants": {
                "type": "nested",
                "properties": {
                    "variant_id": {"type": "keyword"},
                    "sku": {
                        "type": "text",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "price": {"type": "float"},
                    "compare_at_price": {"type": "float"},
                    "stock": {"type": "integer"},
                    "image": {"type": "keyword", "index": False},
                    "weight": {"type": "float"},
                    "weight_unit": {"type": "keyword"},
                    "attributes": {
                        "type": "flattened"  # Allows searching any attribute value
                    }
                }
            }
        }
    },
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "analyzer": {
                "autocomplete": {
                    "type": "custom",
                    "tokenizer": "autocomplete_tokenizer",
                    "filter": ["lowercase"]
                }
            },
            "tokenizer": {
                "autocomplete_tokenizer": {
                    "type": "edge_ngram",
                    "min_gram": 2,
                    "max_gram": 10
                }
            }
        }
    }
}

# Mapping for Enhanced Descriptions (Vector Search)
ENHANCED_DESCRIPTION_MAPPING = {
    "mappings": {
        "properties": {
            "product_id": {"type": "keyword"},
            "original_name": {"type": "text"},
            "generated_description": {"type": "text"},
            "description_embedding": {
                "type": "dense_vector",
                "dims": 1536,  # OpenAI text-embedding-3-small uses 1536 dimensions
                "index": True,
                "similarity": "cosine"
            },
            "updated_at": {"type": "date"}
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
            self.enhanced_index_name = os.getenv("ES_ENHANCED_INDEX_NAME", "product_enhanced_descriptions")
            if not self.client.ping():
                logger.error(f"Could not connect to Elasticsearch at {url}")
        except Exception as e:
            logger.error(f"Elasticsearch initialization error: {e}")

    def check_connection(self) -> bool:
        """Verify that Elasticsearch is reachable."""
        try:
            return self.client.ping()
        except:
            return False

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

    def ensure_enhanced_index_exists(self) -> bool:
        try:
            if not self.client.indices.exists(index=self.enhanced_index_name):
                logger.info(f"Creating index {self.enhanced_index_name} with vector mappings")
                self.client.indices.create(
                    index=self.enhanced_index_name,
                    mappings=ENHANCED_DESCRIPTION_MAPPING["mappings"],
                    settings=ENHANCED_DESCRIPTION_MAPPING["settings"]
                )
            return True
        except Exception as e:
            logger.error(f"Failed to ensure enhanced index exists: {e}")
            return False

    def index_enhanced_description(self, product_id: str, name: str, description: str, embedding: List[float]) -> bool:
        try:
            self.ensure_enhanced_index_exists()
            from datetime import datetime
            doc = {
                "product_id": str(product_id),
                "original_name": name,
                "generated_description": description,
                "description_embedding": embedding,
                "updated_at": datetime.utcnow().isoformat()
            }
            self.client.index(
                index=self.enhanced_index_name,
                id=str(product_id),
                document=doc
            )
            return True
        except Exception as e:
            logger.error(f"Failed to index enhanced description for {product_id}: {e}")
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

    def bulk_index_products(self, products: List[ProductDocument]) -> dict:
        if not products:
            return {"success_count": 0, "failed_count": 0, "failures": []}
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
            
            failed_count = len(errors) if isinstance(errors, list) else 0
            
            if failed_count > 0:
                logger.error(f"Bulk indexing encountered {failed_count} errors")
                
            return {
                "success_count": success_count,
                "failed_count": failed_count,
                "failures": errors if isinstance(errors, list) else []
            }
        except Exception as e:
            logger.error(f"Critical failure during bulk indexing: {e}")
            return {
                "success_count": 0,
                "failed_count": len(products),
                "failures": [{"error": str(e)}]
            }

    def delete_product(self, product_id: Any) -> bool:
        try:
            self.client.delete(index=self.index_name, id=str(product_id))
            # Also try to delete from enhanced index if it exists
            try:
                self.client.delete(index=self.enhanced_index_name, id=str(product_id))
            except:
                pass # Might not exist in enhanced index
            return True
        except Exception as e:
            logger.error(f"Failed to delete product {product_id}: {e}")
            return False

    def delete_enhanced_description(self, product_id: Any) -> bool:
        try:
            self.client.delete(index=self.enhanced_index_name, id=str(product_id))
            return True
        except Exception as e:
            logger.error(f"Failed to delete enhanced description {product_id}: {e}")
            return False

    def lexical_search(self, query: str, size: int = 10):
        """
        Search products including nested variant data (SKU, attributes).
        Uses bool query to combine parent-level and nested variant searches.
        """
        return self.client.search(
            index=self.index_name,
            size=size,
            query={
                "bool": {
                    "should": [
                        # Parent product fields
                        {
                            "multi_match": {
                                "query": query,
                                "fields": [
                                    "name^3",
                                    "description^2",
                                    "brand",
                                    "categories",
                                    "tags"
                                ]
                            }
                        },
                        # Nested variant search - SKU
                        {
                            "nested": {
                                "path": "variants",
                                "query": {
                                    "match": {
                                        "variants.sku": {
                                            "query": query,
                                            "boost": 2
                                        }
                                    }
                                }
                            }
                        },
                        # Nested variant search - Attributes (color, size, etc.)
                        {
                            "nested": {
                                "path": "variants",
                                "query": {
                                    "match": {
                                        "variants.attributes.*": query
                                    }
                                }
                            }
                        }
                    ],
                    "minimum_should_match": 1
                }
            }
        )

    def semantic_search(self, query_vector: List[float], size: int = 10):
        return self.client.search(
            index=self.enhanced_index_name,
            size=size,
            knn={
                "field": "description_embedding",
                "query_vector": query_vector,
                "k": size,
                "num_candidates": 100
            }
        )

    def rrf_merge(self, lex_hits, sem_hits, k=60):
        scores = {}

        for rank, hit in enumerate(lex_hits):
            pid = hit["_id"]
            scores[pid] = scores.get(pid, 0) + 1 / (k + rank)

        for rank, hit in enumerate(sem_hits):
            pid = hit["_id"]
            scores[pid] = scores.get(pid, 0) + 1 / (k + rank)

        return sorted(scores.items(), key=lambda x: x[1], reverse=True)

    def hybrid_search(self, query: str, query_vector: List[float], size: int = 5):
        lex = self.lexical_search(query, size=20)
        sem = self.semantic_search(query_vector, size=20)

        lex_hits = lex["hits"]["hits"]
        sem_hits = sem["hits"]["hits"]

        ranked = self.rrf_merge(lex_hits, sem_hits)

        final_products = []
        for pid, _ in ranked[:size]:
            doc = self.client.get(index=self.index_name, id=pid)
            final_products.append(doc["_source"])

        return final_products

    def search_by_variant_attributes(
        self, 
        attributes: Dict[str, str], 
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        in_stock_only: bool = False,
        size: int = 10
    ) -> List[Dict]:
        """
        Search for products by specific variant attributes (e.g., color: red, size: L).
        
        Args:
            attributes: Dict of attribute name -> value (e.g., {"color": "red", "size": "L"})
            price_min: Minimum variant price filter
            price_max: Maximum variant price filter
            in_stock_only: Only return variants with stock > 0
            size: Number of results
            
        Returns:
            List of products with matching variants highlighted
        """
        # Build nested query for each attribute
        must_clauses = []
        
        for attr_name, attr_value in attributes.items():
            must_clauses.append({
                "match": {
                    "variants.attributes": attr_value
                }
            })
        
        # Add price filter if specified
        if price_min is not None or price_max is not None:
            price_range = {}
            if price_min is not None:
                price_range["gte"] = price_min
            if price_max is not None:
                price_range["lte"] = price_max
            must_clauses.append({
                "range": {"variants.price": price_range}
            })
        
        # Add stock filter
        if in_stock_only:
            must_clauses.append({
                "range": {"variants.stock": {"gt": 0}}
            })
        
        query = {
            "nested": {
                "path": "variants",
                "query": {
                    "bool": {
                        "must": must_clauses
                    }
                },
                "inner_hits": {
                    "size": 10,
                    "name": "matching_variants"
                }
            }
        }
        
        result = self.client.search(
            index=self.index_name,
            size=size,
            query=query
        )
        
        # Format results with matching variants
        products = []
        for hit in result["hits"]["hits"]:
            product = hit["_source"]
            # Attach only the matching variants
            matching = hit.get("inner_hits", {}).get("matching_variants", {}).get("hits", {}).get("hits", [])
            product["_matching_variants"] = [v["_source"] for v in matching]
            products.append(product)
        
        return products

    def get_variant_by_sku(self, sku: str) -> Optional[Dict]:
        """
        Find a specific variant by SKU.
        
        Returns:
            Product with the matching variant, or None
        """
        result = self.client.search(
            index=self.index_name,
            size=1,
            query={
                "nested": {
                    "path": "variants",
                    "query": {
                        "term": {"variants.sku.keyword": sku}
                    },
                    "inner_hits": {"size": 1}
                }
            }
        )
        
        hits = result["hits"]["hits"]
        if not hits:
            return None
            
        product = hits[0]["_source"]
        matching = hits[0].get("inner_hits", {}).get("variants", {}).get("hits", {}).get("hits", [])
        if matching:
            product["_matched_variant"] = matching[0]["_source"]
        return product


# Global instance
es_service = ElasticsearchService()
