from typing import Any, Dict, Optional, Tuple
import re
from utils.logging import get_logger
from base.models import ProductDocument, Variant

logger = get_logger(__name__)

def strip_html(text: Optional[str]) -> Optional[str]:
    """Remove HTML tags from string using simple regex."""
    if text:
        clean = re.compile("<.*?>")
        return re.sub(clean, "", text).strip()
    return text


def normalize_weight(weight: Optional[float], weight_unit: Optional[str]) -> Tuple[Optional[float], str]:
    """
    Normalize weight to grams for consistent storage and display.
    """
    if weight is None:
        return None, "g"
    
    try:
        weight = float(weight)
    except (ValueError, TypeError):
        return None, "g"
    
    if weight == 0:
        return 0.0, "g"
    
    # Normalize unit string
    unit = (weight_unit or "g").lower().strip()
    
    # Conversion factors to grams
    if unit in ("kg", "kgs", "kilogram", "kilograms"):
        return round(weight * 1000, 2), "g"
    elif unit in ("lb", "lbs", "pound", "pounds"):
        return round(weight * 453.592, 2), "g"
    elif unit in ("oz", "ounce", "ounces"):
        return round(weight * 28.3495, 2), "g"
    else:
        # Default/already grams
        return round(weight, 2), "g"


def transform_shopify_product(payload: dict, inventory_data: Optional[Dict[str, Dict[str, Any]]] = None) -> ProductDocument:
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
        
        # Weight handling
        inv_id = str(v.get("inventory_item_id"))
        inv_item = inventory_data.get(inv_id) if inventory_data else None
        
        if inv_item:
            # GraphQL data - already has correct unit from normalize_unit()
            raw_weight = inv_item.get("weight")
            raw_unit = inv_item.get("unit", "g")
        else:
            # REST API fallback
            # IMPORTANT: "grams" field is ALWAYS in grams regardless of weight_unit
            raw_weight = v.get("grams")
            if raw_weight is not None:
                # grams field exists - value is in grams, ignore weight_unit
                raw_unit = "g"
            else:
                # No grams field, use weight + weight_unit
                raw_weight = v.get("weight")
                raw_unit = v.get("weight_unit") or "g"
        
        # Normalize all weights to grams for consistency
        weight, weight_unit = normalize_weight(raw_weight, raw_unit)
        
        variants_list.append(
            Variant(
                variant_id=str(v.get("id")),
                sku=v.get("sku"),
                price=price,
                compare_at_price=compare_at_price,
                stock=qty,
                image=variant_image,
                weight=weight,
                weight_unit=weight_unit,
                attributes=attributes
            )
        )

    # Extract primary image
    primary_image = None
    if payload.get("image"):
        primary_image = payload["image"].get("src")
    elif payload.get("images") and len(payload["images"]) > 0:
        primary_image = payload["images"][0].get("src")
    
    # Extract all images
    all_images = [img.get("src") for img in payload.get("images", []) if img.get("src")]
    
    # Detect if on sale (any variant has compare_at_price > price)
    on_sale = any(
        v.compare_at_price and v.compare_at_price > v.price 
        for v in variants_list
    )
        
    prices = sorted([p for p in prices if p is not None])
    min_price = prices[0] if prices else 0.0
    max_price = prices[-1] if prices else 0.0

    categories = []
    
    # Try to get standard category from "category" object
    std_category = payload.get("category")
    if std_category and isinstance(std_category, dict):
        cat_name = std_category.get("name")
        if cat_name:
            categories.append(cat_name)
    
    # Fallback to product_type if no standard category found
    if not categories and payload.get("product_type"):
        categories.append(payload.get("product_type"))
        
    doc = ProductDocument(
        product_id=str(payload["id"]),
        name=str(payload.get("title", "")),
        description=strip_html(payload.get("body_html")),
        vendor=payload.get("vendor"),
        brand=payload.get("vendor"),
        categories=categories,
        tags=[t.strip() for t in payload.get("tags", "").split(",") if t.strip()],
        slug=payload.get("handle"),
        
        # Calculated
        price_min=min_price,
        price_max=max_price,
        total_inventory=total_inventory,
        status=payload.get("status", "active"),
        on_sale=on_sale,
        
        # Nested Struct
        variants=variants_list,
        
        # Media
        primary_image=primary_image,
        images=all_images
    )
    
    logger.debug(f"Successfully transformed product: {product_id} with {len(variants_list)} variants")
    return doc
