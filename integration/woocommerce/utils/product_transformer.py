from base.models import ProductDocument, Variant
from woocommerce.loggers import get_logger
import re

logger = get_logger("product_transformer")


def strip_html(text):
    """Remove HTML tags from string."""
    if text:
        clean = re.compile("<.*?>")
        return re.sub(clean, "", text).strip()
    return ""


def transform_product_for_es(product: dict) -> ProductDocument:
    """Convert merged WooCommerce product into unified ProductDocument."""
    if not product:
        logger.warning("transform_product_for_es called with empty product")
        raise ValueError("Empty product data")

    product_id = str(product.get("id"))
    
    # Flatten attributes for easier search
    raw_attributes = product.get("attributes", [])
    flat_attributes = {}
    
    if isinstance(raw_attributes, list):
        for attr in raw_attributes:
            name = attr.get("name")
            options = attr.get("options", [])
            if name:
                flat_attributes[name] = options

    # Transform variants
    variants_list = []
    prices = []
    total_inventory = 0
    
    for v in product.get("variants", []):
        try:
            # Handle variant attributes
            variant_raw_attrs = v.get("attributes", [])
            variant_flat_attrs = {}
            if isinstance(variant_raw_attrs, list):
                for attr in variant_raw_attrs:
                    name = attr.get("name")
                    option = attr.get("option")
                    if name:
                        variant_flat_attrs[name] = option

            price = float(v.get("price", 0) or 0)
            prices.append(price)
            
            stock = int(v.get("stock_quantity", 0) if v.get("stock_quantity") is not None else 0)
            total_inventory += stock
            
            variants_list.append(
                Variant(
                    variant_id=str(v.get("id")),
                    sku=v.get("sku"),
                    price=price,
                    compare_at_price=float(v.get("regular_price", 0) or 0) if v.get("sale_price") else None,
                    stock=stock,
                    image=v.get("image", {}).get("src") if isinstance(v.get("image"), dict) else None,
                    attributes=variant_flat_attrs
                )
            )
        except Exception as e:
            logger.error(f"Error transforming variant {v.get('id')}: {e}")

    # Extract images, tags, categories
    images = [img.get("src") for img in product.get("images", []) if isinstance(img, dict) and img.get("src")]
    main_image = images[0] if images else None
    
    tags = [tag.get("name") for tag in product.get("tags", []) if isinstance(tag, dict) and tag.get("name")]
    categories = [cat.get("name") for cat in product.get("categories", []) if isinstance(cat, dict) and cat.get("name")]
    
    prices = sorted([p for p in prices if p is not None])
    min_price = prices[0] if prices else 0.0
    max_price = prices[-1] if prices else 0.0

    return ProductDocument(
        product_id=product_id,
        name=product.get("name", "N/A"),
        description=strip_html(product.get("description")),
        vendor="WooCommerce Store",  # Default for WooCommerce
        brand=None,
        category=", ".join(categories) if categories else None,
        tags=tags,
        price_min=min_price,
        price_max=max_price,
        total_inventory=total_inventory,
        status="active" if product.get("status") == "publish" else "inactive",
        variants=variants_list,
        image=main_image,
        updated_at=product.get("date_modified"),
        created_at=product.get("date_created")
    )
    
