from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class Variant(BaseModel):
    variant_id: str
    sku: Optional[str] = None
    price: float
    compare_at_price: Optional[float] = None
    stock: int
    image: Optional[str] = None
    weight: Optional[float] = None  # Weight in grams
    weight_unit: str = "g"
    attributes: Dict[str, Any] = {}

class ProductDocument(BaseModel):
    product_id: str
    name: str
    description: Optional[str] = None
    vendor: Optional[str] = None
    brand: Optional[str] = None
    categories: List[str] = []  # Changed to list for WooCommerce multi-category support
    tags: List[str] = []
    slug: Optional[str] = None  # URL-friendly identifier
    
    # Calculated fields for search/filtering
    price_min: float
    price_max: float
    currency: str = "NPR"
    total_inventory: int
    status: str
    on_sale: bool = False  # Quick filter for sale items
    
    # Nested variants
    variants: List[Variant]
    
    # Media
    primary_image: Optional[str] = None
    images: List[str] = []  # All product images
    
    # Metadata
    updated_at: Optional[str] = None
    created_at: Optional[str] = None
