"""
Shopify Product Transformation Service

Transforms raw Shopify product JSON into a standardized format
with proper type validation using Pydantic models.
"""

from typing import List, Optional, Dict, Any

from integration.shopify.config import get_product_page_url, get_variant_page_url
from integration.schemas import Product, ProductStatus, ProductVariant
from integration.schemas import ProductDescription, ProductVariantDescription


def _get_image_src_by_id(images: List[Dict[str, Any]], image_id: Optional[int]) -> Optional[str]:
    """
    Find image src from images list by image_id.
    
    Args:
        images: List of image dictionaries from Shopify product
        image_id: Image ID to search for
        
    Returns:
        Image src URL or None if not found
    """
    if not image_id or not images:
        return None
    
    for image in images:
        if image.get("id") == image_id:
            return image.get("src")
    
    return None


def _map_shopify_status(shopify_status: str) -> ProductStatus:
    """
    Map Shopify status to standardized ProductStatus enum.
    
    Args:
        shopify_status: Shopify product status string
        
    Returns:
        ProductStatus enum value
    """
    status_mapping = {
        "active": ProductStatus.ACTIVE,
        "draft": ProductStatus.DRAFT,
        "archived": ProductStatus.UNLISTED,
    }
    
    return status_mapping.get(shopify_status.lower(), ProductStatus.DRAFT)


def _extract_options(shopify_options: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Extract and format product options from Shopify format.
    
    Args:
        shopify_options: List of option dictionaries from Shopify
        
    Returns:
        Dictionary mapping option names to their values
    """
    options = {}
    
    for option in shopify_options:
        name = option.get("name")
        values = option.get("values", [])
        
        if name:
            options[name] = values
    
    return options


def transform_shopify_product(shopify_product: Dict[str, Any], store_url: Optional[str] = None) -> Product:
    """
    Transform raw Shopify product JSON into standardized Product model.
    
    Args:
        shopify_product: Raw Shopify product dictionary
        
    Returns:
        Standardized Product model instance
        
    Example:
        >>> shopify_json = {...}  # Raw Shopify product JSON
        >>> product = transform_shopify_product(shopify_json)
        >>> print(product.product_id, product.title)
    """
    # Extract main product fields
    product_id = shopify_product.get("id")
    title = shopify_product.get("title", "")
    description = shopify_product.get("body_html")
    vendor = shopify_product.get("vendor", "")
    product_type = shopify_product.get("product_type", "")
    tags = shopify_product.get("tags", "")
    handle = shopify_product.get("handle", "")
    product_url = get_product_page_url(store_url=store_url, handle=handle) if store_url else handle
    status = _map_shopify_status(shopify_product.get("status", "draft"))
    
    # Extract options
    shopify_options = shopify_product.get("options", [])
    options = _extract_options(shopify_options)
    
    # Extract main product image
    image = None
    if shopify_product.get("image"):
        image = shopify_product["image"].get("src")
    
    # Get images list for variant image mapping
    images = shopify_product.get("images", [])
    
    # Transform variants
    variants = []
    product_variants = []
    shopify_variants = shopify_product.get("variants", [])
    
    for variant in shopify_variants:
        # Get variant image src if image_id is present
        variant_image_id = variant.get("image_id")
        variant_image_src = _get_image_src_by_id(images, variant_image_id)

        variant_id = variant.get("id")
        variant_url = (
            get_variant_page_url(store_url=store_url, handle=handle, variant_id=variant_id)
            if store_url and handle and variant_id
            else None
        )
        
        transformed_variant = ProductVariant(
            id=variant.get("id"),
            product_id=variant.get("product_id"),
            sku=variant.get("sku"),
            title=variant.get("title", ""),
            price=variant.get("price", "0.00"),
            inventory_policy=variant.get("inventory_policy", "deny"),
            taxable=variant.get("taxable", False),
            inventory_quantity=variant.get("inventory_quantity", 0),
            old_inventory_quantity=variant.get("old_inventory_quantity", 0),
            image_src=variant_image_src,
            variant_url=variant_url,
        )
        
        variants.append(transformed_variant)
        product_variants.append(transformed_variant.title)
    
    # Create and return standardized Product
    product = Product(
        id=product_id,
        title=title,
        description=description,
        vendor=vendor,
        product_type=product_type,
        tags=tags,
        product_variants=product_variants,
        product_url=product_url,
        status=status,
        options=options,
        image=image,
        variants=variants
    )
    
    return product


def transform_shopify_products(
    shopify_products: List[Dict[str, Any]],
    store_url: Optional[str] = None,
) -> List[Product]:
    """
    Transform a list of raw Shopify products into standardized Product models.
    
    Args:
        shopify_products: List of raw Shopify product dictionaries
        
    Returns:
        List of standardized Product model instances
    """
    return [transform_shopify_product(product, store_url=store_url) for product in shopify_products]

def transform_shopify_products_for_description(
    shopify_products: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Transform a list of raw Shopify products into standardized Product models.
    
    Args:
        shopify_products: List of raw Shopify product dictionaries
        
    Returns:
        List of standardized Product model instances
    """
    description_products: List[Dict[str, Any]] = []
    for product in shopify_products:
        variants = product.get("variants") or []
        variant_descriptions = []
        for variant in variants:
            variant_descriptions.append(
                ProductVariantDescription.model_validate(
                    {
                        "sku": variant.get("sku"),
                        "title": variant.get("title", ""),
                        "price": variant.get("price", "0.00"),
                    }
                )
            )

        description_payload = {
            "title": product.get("title", ""),
            "description": product.get("description"),
            "vendor": product.get("vendor", ""),
            "product_type": product.get("product_type", ""),
            "tags": product.get("tags", ""),
            "product_variants": product.get("product_variants") or [],
            "options": product.get("options") or {},
            "variants": [
                (v.model_dump(mode="json") if hasattr(v, "model_dump") else v.dict())
                for v in variant_descriptions
            ],
        }

        validated = ProductDescription.model_validate(description_payload)
        if hasattr(validated, "model_dump"):
            description_products.append(validated.model_dump(mode="json"))
        else:
            description_products.append(validated.dict())

    return description_products
