# ============================================================
# WOOCOMMERCE PRODUCT STORE
# Merges parent products and variants 
# ============================================================

# In-memory store for merged products
import logging
logger = logging.getLogger(__name__)

PRODUCT_STORE = {}


def handle_parent_product(product: dict) -> dict | None:
    """
    Handle parent product webhook (type: variable or simple).
    Creates/updates parent entry with empty variants list if needed.
    """
    product_id = product.get("id")
    if not product_id:
        return None

    # Extract attributes (options like Size, Color)
    attributes = {}
    for attr in product.get("attributes", []):
        attr_name = attr.get("name", "").lower()
        attr_options = attr.get("options", [])
        if attr_name and attr_options:
            attributes[attr_name] = attr_options

    # Preserve existing variants if present
    existing_variants = PRODUCT_STORE.get(product_id, {}).get("variants", [])

    # Merge parent product
    PRODUCT_STORE[product_id] = {
        "id": product_id,
        "name": product.get("name"),
        "slug": product.get("slug"),
        "type": product.get("type"),
        "status": product.get("status"),
        "description": product.get("description") or product.get("short_description"),
        "attributes": attributes,
        "categories": product.get("categories", []),
        "tags": product.get("tags", []),
        "brands": product.get("brands", []),
        "images": product.get("images", []),
        "date_created": product.get("date_created"),
        "date_modified": product.get("date_modified"),
        "variants": existing_variants
    }

    return PRODUCT_STORE[product_id]


def handle_variant_product(variant: dict) -> dict | None:
    """
    Handle variant product webhook (type: variation).
    Appends/updates variant inside parent product.
    """
    parent_id = variant.get("parent_id")
    variant_id = variant.get("id")
    if not parent_id or not variant_id:
        return None

    logger.debug(f"Handling variant: ID={variant_id}, Parent={parent_id}")
    logger.debug(f"Variant Raw Data Snippet: price={variant.get('price')}, stock={variant.get('stock_quantity')}")


    # Create placeholder parent if missing
    if parent_id not in PRODUCT_STORE:
        PRODUCT_STORE[parent_id] = {
            "id": parent_id,
            "name": None,  # Will be updated when parent webhook arrives
            "variants": []
        }

    # Extract variant attributes
    variant_attributes = {}
    for attr in variant.get("attributes", []):
        attr_name = attr.get("name", "").lower()
        attr_option = attr.get("option", "")
        if attr_name and attr_option:
            variant_attributes[attr_name] = attr_option

    # Build variant data
    variant_data = {
        "id": variant_id,
        "sku": variant.get("sku"),
        "attributes": variant_attributes,
        "price": variant.get("price"),
        "regular_price": variant.get("regular_price"),
        "sale_price": variant.get("sale_price"),
        "on_sale": variant.get("on_sale"),
        "weight": variant.get("weight"),
        "image": variant.get("image", {}).get("src") if isinstance(variant.get("image"), dict) else None,
        "stock_status": variant.get("stock_status"),
        "stock_quantity": variant.get("stock_quantity"),
        "purchasable": variant.get("purchasable"),
        "date_modified": variant.get("date_modified"),
    }

    # Remove existing variant with same ID (update case)
    variants = [v for v in PRODUCT_STORE[parent_id].get("variants", []) if v["id"] != variant_id]
    variants.append(variant_data)
    PRODUCT_STORE[parent_id]["variants"] = variants

    return PRODUCT_STORE[parent_id]


def handle_product_delete(product: dict) -> bool:
    """
    Handle product delete webhook.
    Removes product or variant from store.
    """
    product_id = product.get("id")
    product_type = product.get("type")
    parent_id = product.get("parent_id")

    if product_type == "variation" and parent_id:
        # Delete variant from parent
        if parent_id in PRODUCT_STORE:
            variants = [v for v in PRODUCT_STORE[parent_id].get("variants", []) if v["id"] != product_id]
            PRODUCT_STORE[parent_id]["variants"] = variants
    else:
        # Delete entire product
        PRODUCT_STORE.pop(product_id, None)

    return True


def get_product(product_id: int) -> dict | None:
    """Return merged product from store (read-only)."""
    return PRODUCT_STORE.get(product_id)


def get_all_products() -> dict:
    """Return all merged products (read-only)."""
    return PRODUCT_STORE


def find_variant(product_id: int, **attributes) -> dict | None:
    """
    Find a specific variant by attributes.
    Example: find_variant(69, color="Navy Blue", size="32")
    """
    product = PRODUCT_STORE.get(product_id)
    if not product:
        return None

    for variant in product.get("variants", []):
        variant_attrs = variant.get("attributes", {})
        if all(variant_attrs.get(k.lower()) == v for k, v in attributes.items()):
            return variant

    return None
