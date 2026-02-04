from typing import Optional, List, Dict

from pydantic import BaseModel

from enum import Enum


class ProductStatus(str, Enum):
    ACTIVE = "active"
    DRAFT = "draft"
    UNLISTED = "unlisted"


class ProductVariant(BaseModel):
    id: int
    product_id: int
    sku: Optional[str] = None
    title: str
    price: str
    inventory_policy: str
    taxable: bool
    inventory_quantity: int
    old_inventory_quantity: int
    image_src: Optional[str] = None
    variant_url: Optional[str] = None

class Product(BaseModel):
    """Standardized product model"""
    id: int
    title: str
    description: Optional[str] = None
    vendor: str
    product_type: str
    tags: str
    product_variants: List[str]
    product_url: str
    status: ProductStatus
    options: Dict[str, List[str]]
    image: Optional[str] = None
    variants: List[ProductVariant]

# For creating Description of product data
class ProductVariantDescription(BaseModel):
    sku: Optional[str] = None
    title: str
    price: str

class ProductDescription(BaseModel):
    title: str
    description: Optional[str] = None
    vendor: str
    product_type: str
    tags: str
    product_variants: List[str]
    options: Dict[str, List[str]]
    variants: List[ProductVariantDescription]