"""
WooCommerce Product Transformation Service

Transforms raw WooCommerce product JSON into a standardized format
with proper type validation using Pydantic models.
"""

from typing import List, Optional, Dict, Any

from integration.woocommerce.config import get_product_page_url, get_variant_page_url
from integration.schemas import Product, ProductStatus, ProductVariant
from integration.schemas import ProductDescription, ProductVariantDescription


def _get_image_src(images: List[Dict[str, Any]], index: int = 0) -> Optional[str]:
    """
    Get image src from images list by index.
    
    Args:
        images: List of image dictionaries from WooCommerce product
        index: Image index (default 0 for main image)
        
    Returns:
        Image src URL or None if not found
    """
    if not images or index >= len(images):
        return None
    
    return images[index].get("src")


def _map_woocommerce_status(woo_status: str) -> ProductStatus:
    """
    Map WooCommerce status to standardized ProductStatus enum.
    
    Args:
        woo_status: WooCommerce product status string
        
    Returns:
        ProductStatus enum value
    """
    status_mapping = {
        "publish": ProductStatus.ACTIVE,
        "draft": ProductStatus.DRAFT,
        "pending": ProductStatus.DRAFT,
        "private": ProductStatus.UNLISTED,
    }
    
    return status_mapping.get(woo_status.lower(), ProductStatus.DRAFT)


def _extract_options(woo_attributes: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Extract and format product options from WooCommerce attributes.
    
    Args:
        woo_attributes: List of attribute dictionaries from WooCommerce
        
    Returns:
        Dictionary mapping option names to their values
    """
    options = {}
    
    for attr in woo_attributes:
        name = attr.get("name")
        # WooCommerce can have options as array or pipe-separated string
        values = attr.get("options", [])
        
        if name and values:
            if isinstance(values, str):
                values = [v.strip() for v in values.split("|")]
            options[name] = values
    
    return options


def transform_woocommerce_product(woo_product: Dict[str, Any], store_url: Optional[str] = None) -> Product:
    """
    Transform raw WooCommerce product JSON into standardized Product model.
    
    Args:
        woo_product: Raw WooCommerce product dictionary
        store_url: Store URL for building product/variant URLs
        
    Returns:
        Standardized Product model instance
    """
    # Extract main product fields
    product_id = woo_product.get("id")
    title = woo_product.get("name", "")
    description = woo_product.get("description") or woo_product.get("short_description")
    
    # WooCommerce doesn't have vendor, use categories or default
    categories = woo_product.get("categories", [])
    vendor = categories[0].get("name", "") if categories else ""
    
    # Product type mapping
    product_type = woo_product.get("type", "simple")
    
    # Tags - WooCommerce returns as list of objects, convert to comma-separated string
    tags_list = woo_product.get("tags", [])
    tags = ", ".join([tag.get("name", "") for tag in tags_list if tag.get("name")])
    
    product_url = get_product_page_url(store_url=store_url, product_id=product_id) if store_url else str(product_id)
    status = _map_woocommerce_status(woo_product.get("status", "draft"))
    
    # Extract options from attributes
    woo_attributes = woo_product.get("attributes", [])
    options = _extract_options(woo_attributes)
    
    # Extract main product image
    images = woo_product.get("images", [])
    image = _get_image_src(images, 0)
    
    # Transform variants
    variants = []
    product_variants = []
    woo_variations = woo_product.get("variations", [])
    
    # If product has no variations, create a single variant from product data
    if not woo_variations:
        # Simple product - treat as single variant
        variant = ProductVariant(
            id=product_id,
            product_id=product_id,
            sku=woo_product.get("sku"),
            title=title,
            price=str(woo_product.get("price", woo_product.get("regular_price", "0.00"))),
            inventory_policy="deny",
            taxable=woo_product.get("taxable", False),
            inventory_quantity=woo_product.get("stock_quantity", 0) or 0,
            old_inventory_quantity=woo_product.get("stock_quantity", 0) or 0,
            image_src=image,
            variant_url=product_url,
        )
        variants.append(variant)
        product_variants.append(title)
    else:
        for idx, variation in enumerate(woo_variations):
            
            if isinstance(variation, int):
                variation_id = variation
                variant_title = f"{title} - Variation {idx + 1}"
                variant_price = woo_product.get("price", "0.00")
                variant_sku = None
                variant_image = image
            else:
                variation_id = variation.get("id", product_id)
                variant_title = variation.get("name", f"{title} - {variation.get('id', '')}")
                variant_price = variation.get("price", variation.get("regular_price", "0.00"))
                variant_sku = variation.get("sku")
                variant_images = variation.get("images", [])
                variant_image = _get_image_src(variant_images, 0) or image
            
            variant_url = (
                get_variant_page_url(store_url=store_url, product_id=product_id, variation_id=variation_id)
                if store_url and variation_id
                else None
            )
            
            transformed_variant = ProductVariant(
                id=variation_id,
                product_id=product_id,
                sku=variant_sku,
                title=variant_title,
                price=str(variant_price),
                inventory_policy="deny",
                taxable=woo_product.get("taxable", False),
                inventory_quantity=variation.get("stock_quantity", 0) if isinstance(variation, dict) else 0,
                old_inventory_quantity=variation.get("stock_quantity", 0) if isinstance(variation, dict) else 0,
                image_src=variant_image,
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


def transform_woocommerce_products(
    woo_products: List[Dict[str, Any]],
    store_url: Optional[str] = None,
) -> List[Product]:
    """
    Transform a list of raw WooCommerce products into standardized Product models.
    
    Args:
        woo_products: List of raw WooCommerce product dictionaries
        store_url: Store URL for building product/variant URLs
        
    Returns:
        List of standardized Product model instances
    """
    return [transform_woocommerce_product(product, store_url=store_url) for product in woo_products]


def transform_woocommerce_products_for_description(
    woo_products: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Transform WooCommerce products into description-ready format for LLM.
    
    Args:
        woo_products: List of raw WooCommerce product dictionaries
        
    Returns:
        List of ProductDescription-validated dictionaries
    """
    description_products: List[Dict[str, Any]] = []
    for product in woo_products:
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
