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
    
    # Handle both raw WOO attributes (list of dicts) and stored attributes (dict)
    if isinstance(raw_attributes, list):
        for attr in raw_attributes:
            name = attr.get("name")
            options = attr.get("options", [])
            if name:
                flat_attributes[name] = options
    elif isinstance(raw_attributes, dict):
        flat_attributes = raw_attributes

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
            elif isinstance(variant_raw_attrs, dict):
                variant_flat_attrs = variant_raw_attrs

            price = float(v.get("price", 0) or 0)
            prices.append(price)
            
            # Use regular_price as compare_at_price if product is on sale
            reg_price = float(v.get("regular_price", 0) or 0)
            compare_price = reg_price if v.get("on_sale") or v.get("sale_price") else None
            
            stock = int(v.get("stock_quantity", 0) if v.get("stock_quantity") is not None else 0)
            total_inventory += stock
            
            # Resolve image (might be string or dict)
            v_image = v.get("image")
            if isinstance(v_image, dict):
                v_image = v_image.get("src")

            variants_list.append(
                Variant(
                    variant_id=str(v.get("id")),
                    sku=v.get("sku"),
                    price=price,
                    compare_at_price=compare_price,
                    stock=stock,
                    image=v_image,
                    weight=float(v.get("weight", 0) or 0) if v.get("weight") else None,
                    weight_unit="g",  # WooCommerce uses shop settings, default to grams
                    attributes=variant_flat_attrs
                )
            )
        except Exception as e:
            logger.error(f"Error transforming variant {v.get('id')}: {e}")

    # Extract images, tags, categories - handling both raw dicts and strings
    raw_images = product.get("images", [])
    images = []
    for img in raw_images:
        if isinstance(img, dict):
            src = img.get("src")
            if src: images.append(src)
        elif isinstance(img, str):
            images.append(img)
            
    main_image = images[0] if images else None
    
    raw_tags = product.get("tags", [])
    tags = []
    for tag in raw_tags:
        if isinstance(tag, dict):
            name = tag.get("name")
            if name: tags.append(name)
        elif isinstance(tag, str):
            tags.append(tag)

    raw_categories = product.get("categories", [])
    categories = []
    for cat in raw_categories:
        if isinstance(cat, dict):
            name = cat.get("name")
            if name: categories.append(name)
        elif isinstance(cat, str):
            categories.append(cat)
    
    # Get brand from brands array if available
    brands = product.get("brands", [])
    brand = None
    if brands and isinstance(brands, list):
        if isinstance(brands[0], dict):
            brand = brands[0].get("name")
        elif isinstance(brands[0], str):
            brand = brands[0]
    
    prices = sorted([p for p in prices if p is not None])
    min_price = prices[0] if prices else 0.0
    max_price = prices[-1] if prices else 0.0

    return ProductDocument(
        product_id=product_id,
        name=product.get("name", "N/A"),
        description=strip_html(product.get("description")),
        vendor="WooCommerce Store",  # Default for WooCommerce
        brand=brand,
        categories=categories,
        tags=tags,
        slug=product.get("slug"),
        price_min=min_price,
        price_max=max_price,
        total_inventory=total_inventory,
        status="active" if product.get("status") == "publish" else "inactive",
        on_sale=product.get("on_sale", False),
        variants=variants_list,
        primary_image=main_image,
        images=images,
        updated_at=product.get("date_modified"),
        created_at=product.get("date_created")
    )
    
