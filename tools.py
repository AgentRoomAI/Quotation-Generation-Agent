"""Business-logic tool implementations for the quotation agent."""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import uuid

logger = logging.getLogger(__name__)


class ToolContext:
    """Simple execution context passed to every tool."""

    def __init__(self, session: Optional[Dict[str, Any]] = None, db=None, pdf_generator=None):
        self.session = session or {}
        self.db = db
        self.pdf_generator = pdf_generator


def _get_session_cart(context: ToolContext) -> List[Dict[str, Any]]:
    if "cart" not in context.session:
        context.session["cart"] = []
    return context.session["cart"]


def _build_cart_items_from_session(context: ToolContext) -> List[Dict[str, Any]]:
    cart_items = []
    if "cart" not in context.session:
        return cart_items

    for item in context.session["cart"]:
        product = context.db.get_product_by_id(item["product_id"]) if context.db else None
        if product:
            cart_items.append({
                "product_name": product.name,
                "quantity": item["quantity"],
                "unit_price": product.price,
                "gst": product.gst,
            })
    return cart_items


def _calculate_summary(cart_items: List[Dict[str, Any]]) -> Dict[str, float]:
    subtotal = sum(item["unit_price"] * item["quantity"] for item in cart_items)
    gst_total = sum((item["unit_price"] * item["quantity"]) * (item["gst"] / 100) for item in cart_items)
    shipping = 25.0 if subtotal > 0 else 0.0
    grand_total = subtotal + gst_total + shipping
    return {
        "subtotal": round(subtotal, 2),
        "gst_total": round(gst_total, 2),
        "shipping": round(shipping, 2),
        "grand_total": round(grand_total, 2),
    }


def search_products(context: ToolContext, category: Optional[str] = None, filters: Optional[Dict[str, Any]] = None, budget: Optional[float] = None) -> Dict[str, Any]:
    """Search products in the catalog using the available database."""
    if context.db is None:
        return {"products": [], "message": "No database available."}

    products = context.db.list_products()
    matching = []
    for product in products:
        if category and category.lower() not in product.name.lower() and category.lower() not in product.description.lower():
            continue
        if budget is not None and product.price > budget:
            continue
        matching.append({
            "id": product.id,
            "name": product.name,
            "sku": product.sku,
            "price": product.price,
            "description": product.description,
            "stock": product.stock,
        })

    return {"products": matching[:10], "message": f"Found {len(matching)} product(s)."}


def add_to_cart(context: ToolContext, product_id: int, quantity: int = 1) -> Dict[str, Any]:
    """Add a product to the user cart."""
    cart = _get_session_cart(context)
    quantity = max(1, int(quantity))
    cart.append({"product_id": int(product_id), "quantity": quantity})
    return {"message": "Product added to cart.", "cart_size": len(cart)}


def remove_from_cart(context: ToolContext, product_id: int) -> Dict[str, Any]:
    """Remove a product from the cart by product id."""
    cart = _get_session_cart(context)
    new_cart = [item for item in cart if item.get("product_id") != int(product_id)]
    context.session["cart"] = new_cart
    return {"message": "Product removed from cart.", "cart_size": len(new_cart)}


def update_quantity(context: ToolContext, product_id: int, quantity: int) -> Dict[str, Any]:
    """Update the quantity of a cart item."""
    cart = _get_session_cart(context)
    quantity = max(0, int(quantity))
    updated = False
    for item in cart:
        if item.get("product_id") == int(product_id):
            if quantity <= 0:
                cart.remove(item)
            else:
                item["quantity"] = quantity
            updated = True
            break
    return {"message": "Cart updated." if updated else "Item not found in cart.", "cart_size": len(cart)}


def show_cart(context: ToolContext) -> Dict[str, Any]:
    """Show the contents of the current cart."""
    cart_items = _build_cart_items_from_session(context)
    summary = _calculate_summary(cart_items)
    return {"items": cart_items, "summary": summary}


def generate_quotation(context: ToolContext) -> Dict[str, Any]:
    """Generate a quotation summary from the current cart."""
    cart_items = _build_cart_items_from_session(context)
    if not cart_items:
        return {"message": "Cart is empty.", "quotation": None}
    summary = _calculate_summary(cart_items)
    return {"message": "Quotation generated.", "quotation": {"items": cart_items, "summary": summary}}


def generate_pdf(context: ToolContext) -> Dict[str, Any]:
    """Create a PDF quotation when the PDF generator is available."""
    if context.pdf_generator is None:
        return {"message": "PDF generator is not available."}

    cart_items = _build_cart_items_from_session(context)
    if not cart_items:
        return {"message": "Cart is empty."}

    quotation_id = f"QT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    quotation_data = {
        "items": cart_items,
        "subtotal": _calculate_summary(cart_items)["subtotal"],
        "gst_total": _calculate_summary(cart_items)["gst_total"],
        "shipping": _calculate_summary(cart_items)["shipping"],
        "grand_total": _calculate_summary(cart_items)["grand_total"],
    }
    pdf_path = context.pdf_generator.generate(quotation_data, "Customer", quotation_id)
    return {"message": "PDF generated.", "quotation_id": quotation_id, "pdf_name": os.path.basename(pdf_path)}


def clear_cart(context: ToolContext) -> Dict[str, Any]:
    """Clear all items from the cart."""
    context.session["cart"] = []
    return {"message": "Cart cleared.", "cart_size": 0}
