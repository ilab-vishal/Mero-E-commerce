from typing import Dict, Any, List
from utils.logging import get_logger
from shopify.models.product import ProductDocument, Variant

logger = get_logger(__name__)

class ShopifyProductAdapter:
    """
    Adapts Shopify product data to the internal ProductDocument model.
    """
    
    @staticmethod
    def adapt(shopify_product: Dict[str, Any]) -> ProductDocument:
        """
        Convert a Shopify product dictionary to a ProductDocument.
        """
        try:
            # Extract basic fields
            product_id = shopify_product.get("id")
            title = shopify_product.get("title", "Unknown Product")
            vendor = shopify_product.get("vendor", "Unknown Vendor")
            product_type = shopify_product.get("product_type", "Uncategorized")
            body_html = shopify_product.get("body_html", "") or ""
            updated_at = shopify_product.get("updated_at", "")
            tags_str = shopify_product.get("tags", "")
            tags = [t.strip() for t in tags_str.split(",")] if tags_str else []
            
            # Extract image
            images = shopify_product.get("images", [])
            image_url = images[0].get("src") if images else None
            
            # Extract variants
            variants_data = shopify_product.get("variants", [])
            variants: List[Variant] = []
            
            min_price = float('inf')
            max_price = 0.0
            total_inventory = 0
            
            for v_data in variants_data:
                price = float(v_data.get("price", 0.0))
                inventory = int(v_data.get("inventory_quantity", 0) or 0)
                
                # pricing logic
                if price < min_price:
                    min_price = price
                if price > max_price:
                    max_price = price
                
                total_inventory += inventory
                
                # Attributes
                msg_attributes = {}
                # Map option1, option2, etc to names if available (usually requires looking at 'options' field but skipping for MVP)
                # Just storing generic attributes
                if v_data.get("title"):
                    msg_attributes["title"] = v_data.get("title")
                
                variants.append(Variant(
                    size=v_data.get("option1"), # Simplification
                    color=v_data.get("option2"), # Simplification
                    price=price,
                    stock=inventory,
                    attributes=msg_attributes
                ))
            
            if min_price == float('inf'):
                min_price = 0.0
            
            return ProductDocument(
                product_id=product_id,
                name=title,
                vendor=vendor,
                category=product_type,
                description=body_html, # In real app, strip HTML
                price_min=min_price,
                price_max=max_price,
                currency="NPR", # Defaulting as per schema, or check shop MoneyFormat
                total_inventory=total_inventory,
                variants=variants,
                image=image_url,
                tags=tags,
                status=shopify_product.get("status", "unknown"),
                updated_at=updated_at
            )
            
        except Exception as e:
            logger.error(f"Error adapting product {shopify_product.get('id')}: {e}")
            raise
