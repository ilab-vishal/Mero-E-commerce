from __future__ import annotations

from typing import Any, Dict, List, Optional


def normalize_products_for_indexing(
    *,
    provider: str,
    products: List[Dict[str, Any]],
    integration_data: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    provider_key = (provider or "").lower()

    if provider_key == "shopify":
        from integration.shopify.services.shopify_transform_products import (
            transform_shopify_products,
        )

        store_url = (integration_data or {}).get("store_url")
        transformed = transform_shopify_products(products, store_url=store_url)

        normalized_products: List[Dict[str, Any]] = []
        for p in transformed:
            if hasattr(p, "model_dump"):
                normalized_products.append(p.model_dump(mode="json"))
            else:
                normalized_products.append(p.dict())
        return normalized_products

    elif provider_key == "woocommerce":
        from integration.woocommerce.services.woocommerce_transform_products import (
            transform_woocommerce_products,
        )

        store_url = (integration_data or {}).get("store_url")
        transformed = transform_woocommerce_products(products, store_url=store_url)

        normalized_products: List[Dict[str, Any]] = []
        for p in transformed:
            if hasattr(p, "model_dump"):
                normalized_products.append(p.model_dump(mode="json"))
            else:
                normalized_products.append(p.dict())
        return normalized_products

    return products


def normalize_products_for_description(
    *,
    provider: str,
    products: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    provider_key = (provider or "").lower()

    if provider_key == "shopify":
        from integration.shopify.services.shopify_transform_products import (
            transform_shopify_products_for_description,
        )

        return transform_shopify_products_for_description(products)

    elif provider_key == "woocommerce":
        from integration.woocommerce.services.woocommerce_transform_products import (
            transform_woocommerce_products_for_description,
        )

        return transform_woocommerce_products_for_description(products)

    return products
