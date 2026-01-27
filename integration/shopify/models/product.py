from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class Variant(BaseModel):
    size: Optional[str] = None
    color: Optional[str] = None
    price: float
    stock: int
    attributes: Dict[str, Any] = {}

class ProductDocument(BaseModel):
    product_id: int
    name: str
    vendor: str
    category: str
    description: str
    price_min: float
    price_max: float
    currency: str
    total_inventory: int
    variants: List[Variant]
    image: Optional[str] = None
    tags: List[str] = []
    status: str
    updated_at: str
