import os
import json
from typing import List, Optional, Any, Dict
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from utils.logging import get_logger

logger = get_logger(__name__)

class LLMService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY not found in environment")
            self.chat_model = None
            self.embeddings_model = None
            return
            
        # Initialize LangChain Models for OpenAI
        self.chat_model = ChatOpenAI(
            model="gpt-3.5-turbo",
            api_key=api_key,
            temperature=0
        )
        
        self.embeddings_model = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=api_key
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
You are a Professional Data Transcriber. Convert the product JSON into a natural language "Product Knowledge Document" optimized for AI search.

CRITICAL RULES:
1. EXHAUSTIVE COVERAGE: Include every single field, ID, and URL.
2. NO HALLUCINATION: Use ONLY provided JSON facts.
3. STRUCTURE & REDUNDANCY:
   - Start with Product Name, IDs, and Brand.
   - SUMMARY SECTION: Explicitly list all available colors and sizes in one sentence (e.g. "Available in colors Red, Blue and sizes S, M, L"). This is critical for broad searches.
   - DETAILED VARIANTS: List EVERY variant with its ID, SKU, exact Price (with currency), Stock, Color, and Size. 
   - IMAGES: List ALL image URLs from the 'images' list.
4. CLEANING: Remove HTML from the description.
5. NARRATIVE: Write as a single, high-density paragraph.

JSON DATA:
{product_json}

Write the complete, exhaustive product paragraph now:
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
