"""Business-logic tool implementations for the quotation agent."""

import json
import logging
import os
import re
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
    raw = (category or "").lower().strip()
    words = re.findall(r"[a-z0-9]+", raw)
    filler = {"i", "need", "want", "buy", "purchase", "for", "the", "a", "an", "please", "can", "you", "search", "find", "show", "me", "looking", "about", "check", "what", "is", "are", "price", "stock", "available"}
    search_words = [
        w[:-1] if w.endswith("s") and len(w) > 3 and not w.endswith("ss") else w
        for w in words
        if not w.isdigit() and w not in filler
    ]
    if not search_words:
        search_words = [w for w in words if not w.isdigit()] or words

    scored = []
    for product in products:
        if budget is not None and product.price > budget:
            continue

        name_lower = f"{product.name} {product.sku}".lower()
        desc_lower = product.description.lower()
        score = 0

        for w in search_words:
            if w in name_lower:
                score += 10
            elif (
                f"{w} with" in desc_lower
                or f"{w} featuring" in desc_lower
                or f"slim {w}" in desc_lower
                or f"business {w}" in desc_lower
                or f"gaming {w}" in desc_lower
                or f"thin and light {w}" in desc_lower
                or f"reliable {w}" in desc_lower
            ):
                score += 8
            elif f"for {w}" in desc_lower or f"for {w}s" in desc_lower:
                score += 2
            elif w in desc_lower:
                score += 4

        if score > 0 or not search_words:
            scored.append((score, product))

    scored.sort(key=lambda item: (-item[0], item[1].name))
    matching = [
        {
            "id": p.id,
            "name": p.name,
            "sku": p.sku,
            "price": p.price,
            "description": p.description,
            "stock": p.stock,
        }
        for _, p in scored
    ]
    return {"products": matching[:10], "message": f"Found {len(matching)} product(s)."}


def add_to_cart(context: ToolContext, product_id: int, quantity: int = 1) -> Dict[str, Any]:
    """Add a product to the user cart."""
    cart = _get_session_cart(context)
    quantity = max(1, int(quantity))
    for item in cart:
        if item.get("product_id") == int(product_id):
            item["quantity"] += quantity
            return {"message": f"Updated quantity for product {product_id} in cart.", "cart_size": len(cart)}
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
    summary = _calculate_summary(cart_items)
    quotation_data = {
        "items": cart_items,
        "subtotal": summary["subtotal"],
        "gst_total": summary["gst_total"],
        "shipping": summary["shipping"],
        "grand_total": summary["grand_total"],
    }
    customer_name = "Customer"
    if context.session and "customer_name" in context.session:
        customer_name = context.session["customer_name"]
    pdf_path = context.pdf_generator.generate(quotation_data, customer_name, quotation_id)
    pdf_name = os.path.basename(pdf_path)
    if context.session is not None:
        context.session["quotation_id"] = quotation_id
        context.session["quotation_pdf"] = pdf_name
    return {
        "message": "PDF generated.",
        "quotation_id": quotation_id,
        "pdf_name": pdf_name,
        "download_url": f"/pdfs/{pdf_name}",
    }


def clear_cart(context: ToolContext) -> Dict[str, Any]:
    """Clear all items from the cart."""
    context.session["cart"] = []
    return {"message": "Cart cleared.", "cart_size": 0}
