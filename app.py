import os
import re
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory

from chatbot import QuotationChatbot
from database import DatabaseManager
from pdf_generator import QuotationPDFGenerator
from utils import Cart

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "quotation-agent-secret-key")
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "pdfs")

# Initialize shared app services.

chatbot = QuotationChatbot()
db = DatabaseManager()
pdf_generator = QuotationPDFGenerator(output_dir=app.config["UPLOAD_FOLDER"])


def _get_session_cart() -> list[dict]:
    if "cart" not in session:
        session["cart"] = []
    return session["cart"]


def _clear_session_cart() -> None:
    session["cart"] = []


def _calculate_summary(cart_items: list[dict]) -> dict:
    subtotal = sum(item["product"].price * item["quantity"] for item in cart_items)
    gst_total = sum((item["product"].price * item["quantity"]) * (item["product"].gst / 100) for item in cart_items)
    shipping = 25.0 if subtotal > 0 else 0.0
    grand_total = subtotal + gst_total + shipping
    return {
        "subtotal": round(subtotal, 2),
        "gst_total": round(gst_total, 2),
        "shipping": round(shipping, 2),
        "grand_total": round(grand_total, 2),
    }


def _cart_products():
    cart_items = []
    for item in _get_session_cart():
        product = db.get_product_by_id(item["product_id"])
        if product:
            cart_items.append({"product": product, "quantity": item["quantity"]})
    return cart_items


def _build_cart_items_from_session():
    cart_items = []
    if "cart" in session:
        for item in session["cart"]:
            product = db.get_product_by_id(item["product_id"])
            if product:
                cart_items.append({
                    "product_name": product.name,
                    "quantity": item["quantity"],
                    "unit_price": product.price,
                    "gst": product.gst,
                })
    return cart_items


def _generate_quotation_pdf(customer_name: str = "Customer") -> tuple[str, str]:
    cart_items = _build_cart_items_from_session()
    if not cart_items:
        return "", ""

    subtotal = sum(item["unit_price"] * item["quantity"] for item in cart_items)
    gst_total = sum((item["unit_price"] * item["quantity"]) * (item["gst"] / 100) for item in cart_items)
    shipping = 25.0 if subtotal > 0 else 0.0
    grand_total = subtotal + gst_total + shipping
    quotation_id = f"QT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    quotation_data = {
        "items": cart_items,
        "subtotal": subtotal,
        "gst_total": gst_total,
        "shipping": shipping,
        "grand_total": grand_total,
    }
    pdf_path = pdf_generator.generate(quotation_data, customer_name, quotation_id)
    return quotation_id, os.path.basename(pdf_path)


def _find_best_product(term: str):
    normalized_term = term.lower().strip()
    search_terms = [normalized_term]
    if normalized_term.endswith("s"):
        search_terms.append(normalized_term[:-1])
    if normalized_term.endswith("es") and len(normalized_term) > 3:
        search_terms.append(normalized_term[:-2])

    generic_synonyms = {
        "phone": ["phone", "smartphone", "mobile", "android"],
        "phones": ["phone", "smartphone", "mobile", "android"],
        "smartwatch": ["watch", "smartwatch", "fitness"],
        "smart watches": ["watch", "smartwatch", "fitness"],
        "watch": ["watch", "smartwatch", "fitness"],
        "watches": ["watch", "smartwatch", "fitness"],
        "laptop": ["laptop", "notebook"],
        "laptops": ["laptop", "notebook"],
        "printer": ["printer"],
        "printers": ["printer"],
        "monitor": ["monitor"],
        "monitors": ["monitor"],
        "speaker": ["speaker"],
        "speakers": ["speaker"],
        "headphone": ["headphone"],
        "headphones": ["headphone"],
        "earbud": ["earbud"],
        "earbuds": ["earbud"],
        "camera": ["camera"],
        "cameras": ["camera"],
        "console": ["console", "gaming"],
        "consoles": ["console", "gaming"],
        "router": ["router", "wifi"],
        "routers": ["router", "wifi"],
    }

    term_tokens = set(re.findall(r"[a-z0-9]+", normalized_term))
    scored_matches = []
    for product in db.list_products():
        name_text = f"{product.name} {product.sku}".lower()
        description_text = product.description.lower()
        product_tokens = set(re.findall(r"[a-z0-9]+", f"{product.name} {product.description} {product.sku}".lower()))
        score = 0

        if normalized_term and normalized_term in name_text:
            score += 10

        for search_term in search_terms:
            if search_term in name_text:
                score += 4
            elif search_term in description_text:
                score += 1

        if term_tokens:
            score += len(term_tokens & set(re.findall(r"[a-z0-9]+", product.name.lower()))) * 4
            score += len(term_tokens & product_tokens) * 2

        keywords = generic_synonyms.get(normalized_term, [])
        if keywords and any(keyword in f"{product.name} {product.description} {product.sku}".lower() for keyword in keywords):
            score += 2

        if score > 0:
            scored_matches.append((score, product))

    if scored_matches:
        scored_matches.sort(key=lambda item: (-item[0], item[1].name))
        return scored_matches[0][1]

    return None


def _add_products_from_message(message: str):
    parsed = chatbot.parse_message(message)
    requested_items = parsed.get("products", [])
    products_to_add = []

    if requested_items:
        for product_name, quantity in requested_items:
            matched = _find_best_product(product_name)
            if matched:
                products_to_add.append((matched, max(1, quantity)))
    else:
        chunks = [chunk.strip() for chunk in re.split(r"\b(?:and|or|,|;)\b", message.lower()) if chunk.strip()]
        for chunk in chunks:
            quantity_match = re.search(r"(\d+)\s+(.+)", chunk)
            if quantity_match:
                quantity = int(quantity_match.group(1))
                product_name = quantity_match.group(2).strip()
                matched = _find_best_product(product_name)
                if matched:
                    products_to_add.append((matched, max(1, quantity)))
            else:
                matched = _find_best_product(chunk)
                if matched:
                    products_to_add.append((matched, 1))

        if not products_to_add:
            message_words = [word for word in re.findall(r"[a-z0-9]+", message.lower()) if len(word) > 2]
            scored_products = []
            for product in db.list_products():
                haystack = f"{product.name} {product.description} {product.sku}".lower()
                score = sum(1 for word in message_words if word in haystack)
                if score > 0:
                    scored_products.append((score, product))

            scored_products.sort(key=lambda item: (-item[0], item[1].name))
            for _, product in scored_products[:5]:
                products_to_add.append((product, 1))

    return parsed, products_to_add


def _summarize_search_results(message: str) -> list[dict]:
    words = [word for word in re.findall(r"[a-z0-9]+", message.lower()) if len(word) > 2]
    scored_products = []
    for product in db.list_products():
        haystack = f"{product.name} {product.description} {product.sku}".lower()
        score = sum(1 for word in words if word in haystack)
        if score > 0:
            scored_products.append((score, product))

    scored_products.sort(key=lambda item: (-item[0], item[1].name))
    return [
        {
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "stock": product.stock,
        }
        for _, product in scored_products[:5]
    ]


def _search_catalog(query: str) -> list:
    query = (query or "").strip().lower()
    products = db.list_products()
    if not query:
        return products

    matched_products = []
    for product in products:
        haystack = f"{product.name} {product.description} {product.sku}".lower()
        if query in haystack:
            matched_products.append(product)
    return matched_products or db.search_products(query)


@app.route("/", methods=["GET"])
def index():
    _get_session_cart()

    manual_query = request.args.get("q", "").strip()
    products = _search_catalog(manual_query)
    last_message = session.get("last_message", "")
    last_intent = session.get("last_intent", "general")
    last_products = session.get("last_products", [])
    last_suggestions = session.get("last_suggestions", [])
    return render_template(
        "index.html",
        products=products,
        manual_query=manual_query,
        last_message=last_message,
        last_intent=last_intent,
        last_products=last_products,
        last_suggestions=last_suggestions,
    )


@app.route("/search", methods=["GET"])
def search_products():
    return redirect(url_for("index", q=request.args.get("q", "").strip()))


@app.route("/ai-search", methods=["POST"])
def ai_search():
    _get_session_cart()
    message = request.form.get("message", "").strip()
    if not message:
        return redirect(url_for("index"))

    parsed, products_to_add = _add_products_from_message(message)

    if products_to_add:
        cart_items = session["cart"]
        for product, quantity in products_to_add:
            found = False
            for item in cart_items:
                if item["product_id"] == product.id:
                    item["quantity"] += quantity
                    found = True
                    break
            if not found:
                cart_items.append({"product_id": product.id, "quantity": quantity})
        session["cart"] = cart_items

    session["last_products"] = [product.name for product, _ in products_to_add[:3]]
    session["last_message"] = message
    session["last_intent"] = parsed["intent"]
    session["last_suggestions"] = _summarize_search_results(message)
    if products_to_add:
        return redirect(url_for("cart"))
    return redirect(url_for("index"))


@app.route("/add-to-cart/<int:product_id>", methods=["POST"])
def add_to_cart(product_id: int):
    product = db.get_product_by_id(product_id)
    if not product:
        return redirect(url_for("index"))

    cart_items = _get_session_cart()
    quantity = int(request.form.get("quantity", 1))
    found = False
    for item in cart_items:
        if item["product_id"] == product_id:
            item["quantity"] += quantity
            found = True
            break
    if not found:
        cart_items.append({"product_id": product_id, "quantity": quantity})
    session["cart"] = cart_items
    return redirect(url_for("cart"))


@app.route("/add-selected-to-cart", methods=["POST"])
def add_selected_to_cart():
    _get_session_cart()

    selected_products = request.form.getlist("selected_products")
    cart_items = session["cart"]

    for product_id in selected_products:
        product = db.get_product_by_id(int(product_id))
        if not product:
            continue

        quantity = max(1, int(request.form.get(f"quantity_{product_id}", 1)))
        found = False
        for item in cart_items:
            if item["product_id"] == int(product_id):
                item["quantity"] += quantity
                found = True
                break
        if not found:
            cart_items.append({"product_id": int(product_id), "quantity": quantity})

    session["cart"] = cart_items
    return redirect(url_for("cart"))


@app.route("/cart")
def cart():
    cart_items = _cart_products()
    summary = _calculate_summary(cart_items)
    return render_template("cart.html", cart_items=cart_items, **summary)


@app.route("/update-cart/<int:product_id>", methods=["POST"])
def update_cart(product_id: int):
    quantity = int(request.form.get("quantity", 0))
    if "cart" in session:
        session["cart"] = [item for item in session["cart"] if not (item["product_id"] == product_id and quantity <= 0)]
        for item in session["cart"]:
            if item["product_id"] == product_id:
                item["quantity"] = quantity
                break
    return redirect(url_for("cart"))


@app.route("/remove-cart/<int:product_id>")
def remove_cart(product_id: int):
    if "cart" in session:
        session["cart"] = [item for item in session["cart"] if item["product_id"] != product_id]
    return redirect(url_for("cart"))


@app.route("/confirm-quotation", methods=["POST"])
def confirm_quotation():
    customer_name = request.form.get("customer_name", "Customer").strip() or "Customer"
    if not session.get("cart"):
        return redirect(url_for("cart"))

    cart_items = _build_cart_items_from_session()
    if not cart_items:
        return redirect(url_for("cart"))

    subtotal = sum(item["unit_price"] * item["quantity"] for item in cart_items)
    gst_total = sum((item["unit_price"] * item["quantity"]) * (item["gst"] / 100) for item in cart_items)
    shipping = 25.0 if subtotal > 0 else 0.0
    grand_total = subtotal + gst_total + shipping
    quotation_id = f"QT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    quotation_data = {
        "items": cart_items,
        "subtotal": subtotal,
        "gst_total": gst_total,
        "shipping": shipping,
        "grand_total": grand_total,
    }
    pdf_path = pdf_generator.generate(quotation_data, customer_name, quotation_id)

    session["quotation_id"] = quotation_id
    session["quotation_pdf"] = os.path.basename(pdf_path)
    _clear_session_cart()
    return redirect(url_for("quotation"))


@app.route("/quotation")
def quotation():
    pdf_name = session.get("quotation_pdf")
    return render_template(
        "quotation.html",
        quotation_id=session.get("quotation_id"),
        pdf_name=pdf_name,
        download_url=url_for("download_pdf", filename=pdf_name) if pdf_name else None,
    )


@app.route("/pdfs/<path:filename>")
def download_pdf(filename: str):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)


@app.route("/clear-cart", methods=["POST"])
def clear_cart():
    _clear_session_cart()
    return redirect(url_for("cart"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
