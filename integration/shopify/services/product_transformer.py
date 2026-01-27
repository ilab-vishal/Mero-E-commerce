from utils.logging import get_logger
from shopify.models.product import ProductDocument, Variant

logger = get_logger(__name__)


def transform_shopify_product(payload: dict) -> ProductDocument:
    product_id = payload.get("id")
    logger.debug(f"Transforming product payload: {product_id}")
    
    # 1. Map Options (e.g., Option1 -> "Color", Option2 -> "Size")
    option_names = {}
    for opt in payload.get("options", []):
        name = opt.get("name", "").lower().strip()
        position = opt.get("position", 1)
        option_names[f"option{position}"] = name
            
    # Create a map of image_id -> src for quick lookup
    image_map = {img.get("id"): img.get("src") for img in payload.get("images", []) if img.get("id")}
            
    variants_list = []
    prices = []
    total_inventory = 0

    for v in payload.get("variants", []):
        try:
            price = float(v.get("price", 0) or 0)
        except (ValueError, TypeError):
            price = 0.0
            
        prices.append(price)
        
        compare_at = v.get("compare_at_price")
        compare_at_price = float(compare_at) if compare_at else None

        qty = int(v.get("inventory_quantity", 0))
        total_inventory += qty
        
        # Get variant-specific image
        variant_image_id = v.get("image_id")
        variant_image = image_map.get(variant_image_id)
        
        # Resolve dynamic options into attributes map
        attributes = {}
        
        for i in range(1, 4):
            opt_key = f"option{i}"
            val = v.get(opt_key)
            if not val or val == "Default Title":
                continue
                
            name = option_names.get(opt_key, f"Option {i}")
            attributes[name] = val
        
        variants_list.append(
            Variant(
                variant_id=str(v.get("id")),
                sku=v.get("sku"),
                price=price,
                compare_at_price=compare_at_price,
                stock=qty,
                image=variant_image,
                attributes=attributes
            )
        )

    image = None
    if payload.get("image"):
        image = payload["image"].get("src")
    elif payload.get("images") and len(payload["images"]) > 0:
        image = payload["images"][0].get("src")
        
    prices = sorted([p for p in prices if p is not None])
    min_price = prices[0] if prices else 0.0
    max_price = prices[-1] if prices else 0.0

    doc = ProductDocument(
        product_id=payload["id"],
        name=payload.get("title"),
        description=payload.get("body_html"),
        vendor=payload.get("vendor"),
        brand=payload.get("vendor"),
        category=payload.get("product_type"),
        tags=[t.strip() for t in payload.get("tags", "").split(",") if t],
        
        # Calculated
        price_min=min_price,
        price_max=max_price,
        total_inventory=total_inventory,
        status=payload.get("status", "active"),
        
        # Nested Struct
        variants=variants_list,
        
        # Meta
        image=image,
        updated_at=payload.get("updated_at"),
        created_at=payload.get("created_at")
    )
    
    logger.debug(f"Successfully transformed product: {product_id} with {len(variants_list)} variants")
    return doc
