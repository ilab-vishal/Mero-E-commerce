"""LLM Service for chat models and embeddings using LangChain."""

# Standard library imports
import json
from typing import Any, Dict, List, Optional

# Third-party imports
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# Local imports
from config import OPENAI_API_KEY, OPENAI_CHAT_MODEL, OPENAI_EMBEDDING_MODEL, LLM_TEMPERATURE
from utils.logging import get_logger

logger = get_logger(__name__)

class LLMService:
    def __init__(self):
        if not OPENAI_API_KEY:
            logger.error("OPENAI_API_KEY not found in configuration")
            self.chat_model = None
            self.embeddings_model = None
            return
            
        # Initialize LangChain Models using config values
        self.chat_model = ChatOpenAI(
            model=OPENAI_CHAT_MODEL,
            api_key=OPENAI_API_KEY,
            temperature=LLM_TEMPERATURE
        )
        
        self.embeddings_model = OpenAIEmbeddings(
            model=OPENAI_EMBEDDING_MODEL,
            api_key=OPENAI_API_KEY
        )

    def generate_description(self, product_data: Dict[str, Any]) -> Optional[str]:
        """
        Generates a factual "Product Knowledge Document" from the full ProductDocument model.
        This document contains ONLY facts from the data - no hallucination or marketing language.
        Optimized for high-quality embeddings used by our e-commerce chatbot.
        """
        if not self.chat_model:
            return None

        prompt = ChatPromptTemplate.from_template("""
        Role: JSON Transcriber for E-commerce Products

        Task:
        Convert the provided ProductDocument JSON into a single factual paragraph for vector embeddings.
        The output must exactly reflect all values in the JSON and be suitable for embeddings.

        Instructions:
        1. Include all product-level fields: 
        product_id, name, brand, vendor, categories, tags, slug, status, price_min, price_max, currency, 
        total_inventory, on_sale, description, primary_image, images.
        2. For each variant, include: 
        variant_id, sku, price, compare_at_price, stock, weight with weight_unit, attributes (key and value), and image URL.
        3. Include all numbers, text, attribute values, and URLs exactly as they appear in the JSON.
        4. Output all URLs explicitly — primary_image, images array, and each variant image.
        5. Remove HTML but preserve content.
        6. Omit only null or empty fields.
        7. Output a **single continuous paragraph** using short factual sentences.
        8. Do not summarize, paraphrase, or interpret values.
        9. Include everything present in the JSON — no fields should be skipped.

        Product JSON:
        {product_json}
        
        """)

        # Build the chain
        chain = prompt | self.chat_model | StrOutputParser()

        try:
            # We pass the indented JSON to the LLM so it can clearly see the structure
            response = chain.invoke({
                "product_json": json.dumps(product_data, indent=2)
            })
            return response.strip()
        except Exception as e:
            logger.error(f"LLM Knowledge Profile generation failed: {e}")
            return None

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generates a vector embedding using LangChain's OpenAI Embeddings.
        """
        if not self.embeddings_model or not text:
            return None
            
        try:
            return self.embeddings_model.embed_query(text)
        except Exception as e:
            logger.error(f"LangChain OpenAI embedding generation failed: {e}")
            return None

# Global instance
llm_service = LLMService()
