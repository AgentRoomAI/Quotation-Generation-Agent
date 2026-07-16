from dataclasses import dataclass
from typing import Optional


@dataclass
class Product:
    id: int
    name: str
    sku: str
    description: str
    price: float
    stock: int
    gst: float


@dataclass
class CartItem:
    product: Product
    quantity: int
