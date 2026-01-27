# ==========================================================
# PRODUCT TRANSFORMER
# Converts merged WooCommerce product into Elasticsearch-ready document
# ============================================================

from woocommerce.loggers import get_logger
import re

logger = get_logger("product_transformer")


def strip_html(text):
    """Remove HTML tags from string."""
    if text:
        clean = re.compile("<.*?>")
        return re.sub(clean, "", text).strip()
    return ""


def transform_product_for_es(product):
    """Convert merged WooCommerce product into Elasticsearch-ready document."""
    if not product:
        logger.warning("transform_product_for_es called with empty product")
        return {}

    product_id = product.get("id", "unknown")
    logger.debug(f"Transforming product for ES: ID={product_id}")

    # Flatten attributes for easier search
    # WooCommerce returns attributes as a list of objects: [{"name": "Color", "options": ["Red", "Blue"]}]
    raw_attributes = product.get("attributes", [])
    flat_attributes = {}
    
    if isinstance(raw_attributes, list):
        for attr in raw_attributes:
            name = attr.get("name")
            options = attr.get("options", [])
            if name:
                flat_attributes[name] = options
    elif isinstance(raw_attributes, dict):
        # Fallback for unexpected dictionary format
        flat_attributes = {
            k: list(v) if isinstance(v, (list, tuple)) else [v]
            for k, v in raw_attributes.items()
        }

    # Transform variants
    variants = []
    for v in product.get("variants", []):
        try:
            # Handle variant attributes (usually [{"name": "Color", "option": "Red"}])
            variant_raw_attrs = v.get("attributes", [])
            variant_flat_attrs = {}
            
            if isinstance(variant_raw_attrs, list):
                for attr in variant_raw_attrs:
                    name = attr.get("name")
                    option = attr.get("option")
                    if name:
                        variant_flat_attrs[name] = option
            elif isinstance(variant_raw_attrs, dict):
                variant_flat_attrs = variant_raw_attrs

            # Handle cases where price might be empty string or None
            price = v.get("price")
            reg_price = v.get("regular_price")
            sale_price = v.get("sale_price")
            stock = v.get("stock_quantity")
            
            variants.append(
                {
                    "variant_id": str(v.get("id")),
                    "attributes": variant_flat_attrs,
                    "price": float(price) if price and str(price).strip() else 0.0,
                    "regular_price": float(reg_price) if reg_price and str(reg_price).strip() else 0.0,
                    "sale_price": float(sale_price) if sale_price and str(sale_price).strip() else 0.0,
                    "stock_quantity": int(stock) if stock is not None else 0,
                    "stock_status": v.get("stock_status", "instock"),
                }
            )
        except Exception as e:
            logger.error(f"Error transforming variant {v.get('id')}: {e}")
            # Add basic info if full transformation fails
            variants.append({"variant_id": str(v.get("id")), "error": "Transform failed"})

    
    # Extract names from lists of objects for keywords mapping (Elasticsearch expects strings)
    categories = [cat.get("name") for cat in product.get("categories", []) if isinstance(cat, dict) and cat.get("name")]
    if not categories and product.get("categories"):
        # Fallback if categories is already a list of strings
        categories = product.get("categories")

    tags = [tag.get("name") for tag in product.get("tags", []) if isinstance(tag, dict) and tag.get("name")]
    if not tags and product.get("tags"):
        tags = product.get("tags")

    brands = [brand.get("name") for brand in product.get("brands", []) if isinstance(brand, dict) and brand.get("name")]
    if not brands and product.get("brands"):
        brands = product.get("brands")

    images = [img.get("src") for img in product.get("images", []) if isinstance(img, dict) and img.get("src")]
    if not images and product.get("images"):
        # Fallback if images is already a list of strings
        images = product.get("images")

    doc = {
        "product_id": str(product.get("id")),
        "name": product.get("name"),
        "description": strip_html(product.get("description")),
        "short_description": strip_html(product.get("short_description")),
        "categories": categories,
        "tags": tags,
        "brands": brands,
        "images": images,
        "attributes": flat_attributes,
        "variants": variants,
    }
    logger.debug(f"Transformation complete for product {product.get('id', 'unknown')}")
    return doc
    
