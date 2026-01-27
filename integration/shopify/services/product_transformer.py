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
            
    variants = []
    prices = []
    total_inventory = 0

    for v in payload.get("variants", []):
        price = float(v.get("price", 0))
        prices.append(price)
        
        qty = int(v.get("inventory_quantity", 0))
        total_inventory += qty
        
        # Resolve dynamic options
        color_val = None
        size_val = None
        attributes = {}
        
        for i in range(1, 4):
            opt_key = f"option{i}"
            val = v.get(opt_key)
            if not val or val == "Default Title":
                continue
                
            name = option_names.get(opt_key, f"Option {i}")
            attributes[name] = val
            
            # Semantic mapping
            if name in ["color", "colour"]:
                color_val = val
            elif name in ["size", "sizing"]:
                size_val = val
        
        # Fallback for simple "Option 1" / "Option 2" if no names were provided
        if not color_val and not size_val and not option_names:
             color_val = v.get("option1")
             size_val = v.get("option2")

        variants.append(
            Variant(
                size=size_val,
                color=color_val,
                price=price,
                stock=qty,
                attributes=attributes
            )
        )

    image = None
    if payload.get("image"):
        image = payload["image"].get("src")
        
    prices = sorted(prices) if prices else [0.0]

    doc = ProductDocument(
        product_id=payload["id"],
        name=payload.get("title"),
        vendor=payload.get("vendor"),
        
        # Semantics
        category=payload.get("product_type"), # Mapping product_type -> category
        description=payload.get("body_html"), # Mapping body_html -> description
        
        # Pricing
        price_min=prices[0],
        price_max=prices[-1],
        currency="NPR", # Default per schema

        # Inventory
        total_inventory=total_inventory,
        variants=variants,
        
        # Media
        image=image,
        
        # Discovery
        tags=[t.strip() for t in payload.get("tags", "").split(",") if t],
        
        # Freshness
        status=payload.get("status", "unknown"),
        updated_at=payload.get("updated_at"),
    )
    
    logger.debug(f"Successfully transformed product: {product_id} with {len(variants)} variants")
    return doc
