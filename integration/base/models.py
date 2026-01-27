from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class Variant(BaseModel):
    variant_id: str
    sku: Optional[str] = None
    price: float
    compare_at_price: Optional[float] = None
    stock: int
    image: Optional[str] = None
    attributes: Dict[str, Any] = {}

class ProductDocument(BaseModel):
    product_id: str
    name: str
    description: Optional[str] = None
    vendor: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = []
    
    # Calculated fields for search/filtering
    price_min: float
    price_max: float
    currency: str = "NPR"
    total_inventory: int
    status: str
    
    # Nested variants
    variants: List[Variant]
    
    # Media & Metadata
    image: Optional[str] = None
    updated_at: Optional[str] = None
    created_at: Optional[str] = None
