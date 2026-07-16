from typing import Dict, List

from models import CartItem, Product


class Cart:
    def __init__(self):
        self.items: List[CartItem] = []

    def add_item(self, product: Product, quantity: int = 1) -> None:
        for item in self.items:
            if item.product.id == product.id:
                item.quantity += quantity
                return
        self.items.append(CartItem(product=product, quantity=quantity))

    def remove_item(self, product_id: int) -> None:
        self.items = [item for item in self.items if item.product.id != product_id]

    def update_quantity(self, product_id: int, quantity: int) -> None:
        for item in self.items:
            if item.product.id == product_id:
                if quantity <= 0:
                    self.remove_item(product_id)
                else:
                    item.quantity = quantity
                return

    def get_summary(self) -> Dict[str, float]:
        subtotal = sum(item.product.price * item.quantity for item in self.items)
        gst_total = sum((item.product.price * item.quantity) * (item.product.gst / 100) for item in self.items)
        shipping = 25.0 if subtotal > 0 else 0.0
        grand_total = subtotal + gst_total + shipping
        return {
            "subtotal": round(subtotal, 2),
            "gst_total": round(gst_total, 2),
            "shipping": round(shipping, 2),
            "grand_total": round(grand_total, 2),
        }

    def count(self) -> int:
        return sum(item.quantity for item in self.items)
