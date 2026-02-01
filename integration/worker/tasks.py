from worker.celery_app import celery_app
from base.llm_service import llm_service
from base.elasticsearch_service import es_service
from utils.logging import get_logger
import traceback

logger = get_logger(__name__)

@celery_app.task(
    name="worker.tasks.enhance_product_description",
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def enhance_product_description(self, product_data: dict):
    """
    Background task to generate enhanced description and embeddings using OpenAI.
    """
    # Expects a dictionary representation of the ProductDocument model
    product_id = str(product_data.get("product_id"))
    name = product_data.get("name")

    logger.info(f"Starting comprehensive enrichment for product: {product_id} - {name}")

    try:
        # 1. Generate ultimate "Knowledge Profile" using the full product model
        enhanced_description = llm_service.generate_description(product_data)
        if not enhanced_description:
            logger.error(f"Failed to generate description for {product_id}")
            return False

        # 2. Generate Embedding for the new description
        embedding = llm_service.generate_embedding(enhanced_description)
        if not embedding:
            logger.error(f"Failed to generate embedding for {product_id}")
            return False

        # 3. Store in Elasticsearch
        success = es_service.index_enhanced_description(
            product_id=product_id,
            name=name,
            description=enhanced_description,
            embedding=embedding
        )

        if success:
            logger.info(f"Successfully enriched and indexed product {product_id}")
            return True
        else:
            logger.error(f"Failed to index enriched description for {product_id}")
            return False

    except Exception as e:
        logger.error(f"Error in enhance_product_description task: {e}")
        logger.error(traceback.format_exc())
        # Retry the task
        raise self.retry(exc=e)
