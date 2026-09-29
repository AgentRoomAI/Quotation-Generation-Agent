import os
import re
import uuid
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from typing import List, Dict, Tuple, Optional, Any

from agent import QuotationAgent
from chatbot import QuotationChatbot
from database import DatabaseManager
from llm import HuggingFaceToolLLM
from models import Product
from pdf_generator import QuotationPDFGenerator
from tools import ToolContext
from utils import Cart

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "quotation-agent-secret-key")
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "pdfs")

# Configure basic logging for debugging and production observability
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize shared app services.

chatbot = QuotationChatbot()
db = DatabaseManager()
pdf_generator = QuotationPDFGenerator(output_dir=app.config["UPLOAD_FOLDER"])
from qwen_bot import QwenBot
qwen_bot = QwenBot()


def _get_session_cart() -> List[Dict]:
    if "cart" not in session:
        session["cart"] = []
    return session["cart"]


def _clear_session_cart() -> None:
    session["cart"] = []


def _calculate_summary(cart_items: List[Dict]) -> Dict[str, float]:
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


def _generate_quotation_pdf(customer_name: str = "Customer") -> Tuple[str, str]:
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
    matches = _find_best_products(term, limit=1)
    return matches[0] if matches else None


def _find_best_products(term: str, limit: int = 1):
    """Return up to `limit` distinct products that best match `term`."""
    if not term or limit <= 0:
        return []

    normalized_term = term.lower().strip()
    words = re.findall(r"[a-z0-9]+", normalized_term)
    alpha_words = [
        w[:-1] if w.endswith("s") and len(w) > 3 and not w.endswith("ss") else w
        for w in words
        if not w.isdigit()
    ]
    if not alpha_words:
        alpha_words = words

    scored_matches = []
    for product in db.list_products():
        name_lower = f"{product.name} {product.sku}".lower()
        desc_lower = product.description.lower()
        score = 0

        for w in alpha_words:
            if len(w) <= 2:
                in_name = bool(re.search(rf"\b{re.escape(w)}\b", name_lower))
                in_desc = bool(re.search(rf"\b{re.escape(w)}\b", desc_lower))
            else:
                in_name = w in name_lower
                in_desc = w in desc_lower

            if in_name:
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
            elif in_desc:
                score += 4

        if score > 0:
            scored_matches.append((score, product))

    if not scored_matches:
        return []

    scored_matches.sort(key=lambda item: (-item[0], item[1].name))
    return [p for _, p in scored_matches[:limit]]


def _add_products_from_message(message: str):
    parsed = chatbot.parse_message(message)
    requested_items = parsed.get("products", [])
    products_to_add = []

    if requested_items:
        for product_name, quantity in requested_items:
            quantity = max(1, quantity)
            if quantity == 1:
                matched = _find_best_product(product_name)
                if matched:
                    products_to_add.append((matched, 1))
            else:
                # Try to find up to `quantity` distinct products matching the term.
                matches = _find_best_products(product_name, limit=quantity)
                if matches:
                    for m in matches:
                        products_to_add.append((m, 1))
                else:
                    # No distinct matches — fall back to the single best product once.
                    best = _find_best_product(product_name)
                    if best:
                        products_to_add.append((best, 1))
    else:
        chunks = [chunk.strip() for chunk in re.split(r"\b(?:and|or|,|;)\b", message.lower()) if chunk.strip()]
        for chunk in chunks:
            quantity_match = re.search(r"(\d+)\s+(.+)", chunk)
            if quantity_match:
                quantity = max(1, int(quantity_match.group(1)))
                product_name = quantity_match.group(2).strip()
                if quantity == 1:
                    matched = _find_best_product(product_name)
                    if matched:
                        products_to_add.append((matched, 1))
                else:
                    matches = _find_best_products(product_name, limit=quantity)
                    if matches:
                        for m in matches:
                            products_to_add.append((m, 1))
                    else:
                        best = _find_best_product(product_name)
                        if best:
                            products_to_add.append((best, 1))
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


def _summarize_search_results(message: str) -> List[Dict]:
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


CATEGORIES = {
    "laptop": ["laptop", "laptops", "notebook", "notebooks", "macbook", "macbooks"],
    "computer": ["computer", "computers", "desktop", "desktops", "pc", "pcs", "workstation", "workstations", "all-in-one", "aio"],
    "ac": ["ac", "acs", "air conditioner", "airconditioner", "air conditioners", "split ac", "window ac", "inverter ac"],
    "monitor": ["monitor", "monitors", "display", "displays", "screen", "screens"],
    "phone": ["phone", "phones", "smartphone", "smartphones", "mobile", "mobiles", "iphone", "iphones", "galaxy", "pixel"],
    "printer": ["printer", "printers", "printing"],
    "headphone": ["headphone", "headphones", "earbud", "earbuds", "earphone", "earphones", "headset", "headsets", "audio"],
    "speaker": ["speaker", "speakers", "soundbar"],
    "mouse": ["mouse", "mice"],
    "keyboard": ["keyboard", "keyboards"],
    "router": ["router", "routers", "wifi", "mesh", "switch", "switches", "networking"],
    "storage": ["storage", "ssd", "ssds", "hdd", "hdds", "hard drive", "hard drives"],
    "camera": ["camera", "cameras"],
    "controller": ["controller", "controllers"],
    "smartwatch": ["watch", "smartwatch", "tracker"],
}

CATEGORY_EXCLUSIONS = {
    "ac": [
        "phone", "smartphone", "mobile", "laptop", "notebook", "macbook", "desktop", "tower",
        "monitor", "keyboard", "mouse", "watch", "camera", "headphone", "earbud", "speaker",
        "console", "switch", "router", "ssd", "hdd", "printer", "tablet", "acer"
    ],
    "computer": [
        "laptop", "notebook", "macbook", "phone", "smartphone", "mobile", "ac", "air conditioner",
        "watch", "camera", "headphone", "earbud", "speaker", "printer", "tablet"
    ],
    "laptop": [
        "desktop", "tower", "all-in-one", "phone", "smartphone", "mobile", "ac", "air conditioner",
        "hub", "dock", "cable", "nv2", "ssd", "charger", "plug", "case", "bag", "watch", "camera"
    ],
    "phone": [
        "laptop", "desktop", "ac", "air conditioner", "headphone", "earphone", "earbud",
        "watch", "camera", "printer", "router", "switch", "monitor"
    ],
    "monitor": [
        "laptop", "desktop", "phone", "ac", "air conditioner", "watch", "camera"
    ],
    "printer": [
        "laptop", "desktop", "phone", "ac", "air conditioner", "watch", "camera"
    ],
}

CATEGORY_CONSULTATION = {
    "ac": {
        "title": "Air Conditioners (AC)",
        "budget_hint": "e.g., budget-friendly 1-Ton under ₹30,000, mid-range 1.5-Ton ₹35,000 – ₹45,000, or heavy-duty 2-Ton above ₹50,000",
        "specs_prompt": "Room / Cabin Size & Specifications:",
        "specs_hint": "What is the cooling capacity or room size required? (e.g., 1.0 Ton for small cabins up to 120 sq ft, 1.5 Ton for standard office rooms 150-200 sq ft, or 2.0 Ton for large conference rooms; 3-Star or 5-Star inverter)",
        "brands_hint": "Voltas, Daikin, LG, Blue Star, Panasonic, or Lloyd",
    },
    "computer": {
        "title": "Desktop Computers & Workstations",
        "budget_hint": "e.g., budget office PC under ₹50,000, mid-range tower ₹50,000 – ₹90,000, or heavy workstation above ₹1,00,000",
        "specs_prompt": "Primary Workload & Specifications:",
        "specs_hint": "What tasks will these machines handle? (e.g., administrative office workflows, software engineering, finance/data processing, or 3D graphics/CAD)",
        "brands_hint": "Dell, HP, Lenovo, Apple, or Asus",
    },
    "laptop": {
        "title": "Enterprise Laptops",
        "budget_hint": "e.g., budget-friendly under ₹50,000, mid-range ₹50,000 – ₹1,00,000, or premium enterprise above ₹1,00,000",
        "specs_prompt": "Primary Workload & Specifications:",
        "specs_hint": "What tasks will these devices primarily handle? (e.g., software engineering, data science, graphics/video editing, standard administration, or executive mobility)",
        "brands_hint": "Acer, Asus, Apple, Dell, HP, or Lenovo",
    },
    "monitor": {
        "title": "Monitors & Displays",
        "budget_hint": "e.g., Full HD under ₹15,000, QHD/gaming ₹20,000 – ₹30,000, or 4K Ultra HD above ₹30,000",
        "specs_prompt": "Display Specifications & Use Case:",
        "specs_hint": "What screen size and resolution do you need? (e.g., 24-inch or 27-inch; Full HD, QHD, or 4K; dual-screen office productivity or high-refresh creator setup)",
        "brands_hint": "Samsung, LG, Dell, or MSI",
    },
    "phone": {
        "title": "Smartphones & Mobile Devices",
        "budget_hint": "e.g., field operations under ₹25,000, mid-range ₹25,000 – ₹45,000, or flagship above ₹50,000",
        "specs_prompt": "Key Features & Use Case:",
        "specs_hint": "What features are priority? (e.g., long battery life, 5G connectivity, durable build for field logistics, or high-performance executive device)",
        "brands_hint": "Samsung, Apple, OnePlus, Google, or Xiaomi",
    },
    "printer": {
        "title": "Printers & Office Scanners",
        "budget_hint": "e.g., laser printer under ₹15,000, multifunction all-in-one ₹15,000 – ₹30,000, or enterprise network printer above ₹30,000",
        "specs_prompt": "Printing Volume & Features:",
        "specs_hint": "What are your printing needs? (e.g., monochrome vs color, duplex auto-printing, Wi-Fi networking, or scan/copy multifunction)",
        "brands_hint": "Canon, HP, or Epson",
    },
}


def _detect_category(text: str) -> Optional[str]:
    t = text.lower()
    # Check whole word matching for category keywords
    for cat, keywords in CATEGORIES.items():
        if any(re.search(rf"\b{re.escape(k)}\b", t) for k in keywords):
            return cat
    return None


def _extract_budget(text: str) -> Optional[float]:
    t = text.lower().replace(",", "")
    b = re.search(r"(?:budget|price|under|below|around|within|upto|up to|cost|max|maximum)\s*(?:of|is|around|:)?\s*₹?\s*(\d{4,7})\b", t)
    if b:
        return float(b.group(1))
    n = re.search(r"\b(\d{5,7})\b", t)
    if n:
        return float(n.group(1))
    lakh = re.search(r"(\d+(?:\.\d+)?)\s*(?:lakh|lac|l)s?\b", t)
    if lakh:
        return float(lakh.group(1)) * 100000.0
    k = re.search(r"\b(\d+(?:\.\d+)?)\s*k\b", t)
    if k and k.group(1) not in ["4", "8"]:
        return float(k.group(1)) * 1000.0
    if any(w in t for w in ["cheap", "budget-friendly", "affordable", "low cost", "entry-level", "entry level"]):
        return 50000.0
    if any(w in t for w in ["premium", "flagship", "high-end", "high end", "expensive", "workstation"]):
        return 150000.0
    return None


def _extract_quantity(text: str) -> int:
    t = text.lower()
    # 1. Explicit unit markers: e.g. "5 units", "10 pcs", "3x", "5 items", "quantity 5", "qty: 3"
    unit_m = re.search(r"\b(\d+)\s*(?:units?|pieces?|pcs?|items?|nos?|x)\b", t)
    if unit_m and int(unit_m.group(1)) < 2000:
        return max(1, int(unit_m.group(1)))

    # 2. Action verbs + count: "procuring 8", "buying 5", "order of 10", "need 10"
    action_m = re.search(
        r"(?:quantity|qty|order|ordering|procure|procuring|procurement|buying|count|need|needing|want|wanting|require|requiring)\s*(?:of|for|:|=)?\s*(\d+)\b",
        t,
    )
    if action_m and int(action_m.group(1)) < 2000:
        return max(1, int(action_m.group(1)))

    # 3. Product count: "10 laptops", "8 4k monitors", "5 computers", "4 acs", "15 smartphones"
    prod_count_m = re.search(
        r"\b(\d+)\s+(?:[a-z0-9\-]+\s+)*(?:laptops?|computers?|desktops?|pcs?|workstations?|acs?|air\s*conditioners?|monitors?|phones?|smartphones?|printers?|mice|mouses?|keyboards?|headphones?|routers?|screens?|devices?)\b",
        t,
    )
    if prod_count_m and int(prod_count_m.group(1)) < 2000:
        return max(1, int(prod_count_m.group(1)))

    return 1


def _detect_specific_product(text: str) -> Optional[Product]:
    t = text.lower()
    for p in db.list_products():
        if len(p.name) > 3 and p.name.lower() in t:
            return p
        if p.sku and len(p.sku) > 2 and re.search(rf"\b{re.escape(p.sku.lower())}\b", t):
            return p
    return None


def _recommend_product(category: str, budget: Optional[float], text: str, qty: int = 1) -> Tuple[Optional[Product], List[Product]]:
    t = text.lower()
    all_prods = db.list_products()
    cat_keywords = CATEGORIES.get(category, [category])
    exclusions = CATEGORY_EXCLUSIONS.get(category, [])

    cat_items = []
    for p in all_prods:
        p_name = p.name.lower()
        p_desc = p.description.lower()
        p_full = f"{p_name} {p_desc}"

        # Strict isolation for AC category
        if category == "ac":
            is_ac = (
                bool(re.search(r"\b(?:ac|acs|split ac|inverter ac|air conditioner|air conditioners)\b", p_name, re.I))
                or "air conditioner" in p_desc
            )
            # Never treat Acer laptops, MacBooks, phones, desktops, or other electronics as AC
            if not is_ac or any(w in p_name for w in ["acer", "macbook", "action", "phone", "smartphone", "laptop", "desktop", "monitor", "watch", "camera"]):
                continue
            cat_items.append(p)
            continue

        # Strict isolation for Computer (Desktop) category
        if category == "computer":
            is_computer = (
                any(w in p_name for w in ["desktop", "tower", "all-in-one", "mac mini", "imac", "workstation"])
                or "desktop computer" in p_desc
            )
            if not is_computer or any(w in p_name for w in ["laptop", "macbook", "notebook", "phone", "smartphone", "air conditioner", "split ac"]):
                continue
            cat_items.append(p)
            continue

        # Strict isolation for Laptop category
        if category == "laptop":
            is_laptop = any(w in p_name for w in ["laptop", "macbook", "notebook", "aspire", "vivobook", "thinkpad", "inspiron", "victus", "loq", "katana", "zephyrus"])
            if not is_laptop or any(w in p_name for w in ["desktop", "tower", "all-in-one", "hub", "dock", "cable", "nv2", "ssd", "charger", "plug", "case", "bag"]):
                continue
            cat_items.append(p)
            continue

        # General category match
        matches_cat = any(re.search(rf"\b{re.escape(k)}\b", p_full) for k in cat_keywords)
        if not matches_cat:
            continue

        # Check negative exclusions
        if any(re.search(rf"\b{re.escape(ex)}\b", p_name) for ex in exclusions):
            continue

        cat_items.append(p)

    if not cat_items:
        fallback_items = _find_best_products(category, limit=8)
        cat_items = [
            p for p in fallback_items
            if not any(re.search(rf"\b{re.escape(ex)}\b", p.name.lower()) for ex in exclusions)
        ]

    scored = []
    for p in cat_items:
        score = 0.0
        # Budget adherence
        if budget is not None:
            if p.price <= budget:
                # Within budget: rewarded, closer to budget gets slight preference
                diff_ratio = (budget - p.price) / max(1.0, budget)
                score += 60.0 - (diff_ratio * 12.0)
            else:
                # Exceeds budget: penalized proportionally, but lowest-priced available still wins among options
                over_ratio = (p.price - budget) / max(1.0, budget)
                score += 25.0 - (over_ratio * 70.0)

        # Brand preference
        for b in [
            "apple", "macbook", "asus", "acer", "dell", "hp", "lenovo", "samsung", "lg",
            "sony", "canon", "logitech", "kingston", "wd", "voltas", "daikin", "blue star",
            "panasonic", "hitachi", "lloyd"
        ]:
            if b in t and (b in p.name.lower() or b in p.description.lower()):
                score += 60.0

        # Workload & technical specifications
        if any(w in t for w in ["dev", "software", "engineering", "coding", "gaming", "graphics", "rtx", "performance", "speed", "workstation"]):
            if any(w in p.description.lower() for w in ["rtx", "gaming", "performance", "m2", "m3", "workstation", "geforce"]):
                score += 35.0
        if any(w in t for w in ["office", "admin", "basic", "budget", "affordable", "light", "everyday"]):
            if p.price < 55000 or any(w in p.name.lower() for w in ["optiplex", "pro tower", "vivobook", "inspiron", "thinkcentre"]):
                score += 30.0
        if any(w in t for w in ["inverter", "energy", "star", "split", "cooling", "smart", "wifi", "copper", "ton"]):
            if any(w in p.description.lower() for w in ["inverter", "5-star", "energy-efficient", "cooling", "smart", "dual inverter"]):
                score += 30.0
        if any(w in t for w in ["1 ton", "1.0 ton", "1ton"]):
            if "1.0 ton" in p.name.lower() or "1 ton" in p.description.lower():
                score += 45.0
        if any(w in t for w in ["1.5 ton", "1.5ton"]):
            if "1.5 ton" in p.name.lower() or "1.5 ton" in p.description.lower():
                score += 45.0
        if any(w in t for w in ["2 ton", "2.0 ton", "2ton"]):
            if "2.0 ton" in p.name.lower() or "2 ton" in p.description.lower():
                score += 45.0

        if p.stock >= qty:
            score += 15.0

        scored.append((score, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    best = scored[0][1] if scored else None
    alts = [x[1] for x in scored[1:4]] if len(scored) > 1 else []
    return best, alts


def _search_catalog(query: str) -> list:
    q = (query or "").strip().lower()
    all_prods = db.list_products()
    if not q:
        return all_prods

    # Extract budget if present in query (e.g. "ac under 30k", "laptop under 50000")
    budget = _extract_budget(q)

    # Detect category intent
    is_ac_query = bool(re.search(r"\b(?:ac|acs|air\s*conditioners?|split\s*ac|inverter\s*ac)\b", q))
    is_computer_query = bool(re.search(r"\b(?:computers?|desktops?|pcs?|workstations?|all-in-one|aio)\b", q))
    is_laptop_query = bool(re.search(r"\b(?:laptops?|notebooks?|macbooks?)\b", q))
    is_phone_query = bool(re.search(r"\b(?:phones?|smartphones?|mobiles?|iphones?|galaxy)\b", q))

    # Tokenize search query
    stop_words = {"i", "need", "want", "buy", "purchase", "for", "the", "a", "an", "please", "show", "search", "under", "below", "budget", "price", "in", "of", "with"}
    tokens = [w for w in re.findall(r"[a-z0-9]+", q) if w not in stop_words and len(w) > 1]
    if not tokens:
        tokens = [w for w in re.findall(r"[a-z0-9]+", q) if len(w) > 1]

    scored = []
    for p in all_prods:
        p_name = p.name.lower()
        p_desc = p.description.lower()
        p_sku = p.sku.lower()

        # Budget filter (allow 5% margin)
        if budget is not None and p.price > budget * 1.05:
            continue

        # Strict isolation for AC query
        if is_ac_query:
            is_ac_prod = (
                bool(re.search(r"\b(?:ac|acs|split ac|inverter ac|air conditioner|air conditioners)\b", p_name))
                or "air conditioner" in p_desc
            )
            if not is_ac_prod or any(w in p_name for w in ["acer", "macbook", "phone", "desktop", "monitor", "watch", "camera"]):
                continue

        # Strict isolation for Computer query (unless laptop explicitly mentioned)
        if is_computer_query and not is_laptop_query:
            is_comp_prod = (
                any(w in p_name for w in ["desktop", "tower", "all-in-one", "mac mini", "imac", "workstation"])
                or "desktop computer" in p_desc
            )
            if not is_comp_prod or any(w in p_name for w in ["laptop", "macbook", "notebook", "phone", "air conditioner"]):
                continue

        # Strict isolation for Laptop query
        if is_laptop_query and not is_computer_query:
            is_lap_prod = any(w in p_name for w in ["laptop", "macbook", "notebook", "aspire", "vivobook", "thinkpad", "inspiron", "victus", "loq", "katana", "zephyrus"])
            if not is_lap_prod or any(w in p_name for w in ["desktop", "tower", "all-in-one", "phone", "air conditioner"]):
                continue

        score = 0
        # Exact full query match
        if q in p_name:
            score += 100
        elif q in p_desc:
            score += 40

        # SKU match
        if q == p_sku or any(t == p_sku for t in tokens):
            score += 80

        # Token matching with category alias expansion
        matched_tokens = 0
        for t in tokens:
            t_aliases = [t]
            if t in ["ac", "air"]:
                t_aliases.extend(["split ac", "inverter ac", "air conditioner"])
            elif t in ["pc", "computer", "desktop"]:
                t_aliases.extend(["pc", "computer", "desktop", "tower", "all-in-one", "workstation"])
            elif t in ["laptop", "notebook"]:
                t_aliases.extend(["laptop", "notebook", "macbook"])
            elif t in ["phone", "mobile"]:
                t_aliases.extend(["phone", "mobile", "smartphone"])

            token_matched = False
            for alias in t_aliases:
                if alias == "ac":
                    if re.search(r"\b(?:ac|acs|split ac|inverter ac|air conditioner)\b", p_name):
                        score += 40
                        token_matched = True
                        break
                elif len(alias) <= 2:
                    if re.search(rf"\b{re.escape(alias)}\b", p_name):
                        score += 35
                        token_matched = True
                        break
                elif alias in p_name:
                    score += 30
                    token_matched = True
                    break
                elif alias in p_desc:
                    score += 10
                    token_matched = True
                    break
            if token_matched:
                matched_tokens += 1

        if matched_tokens == len(tokens) and len(tokens) > 1:
            score += 100

        if score > 0:
            scored.append((score, p))

    scored.sort(key=lambda item: (-item[0], item[1].price))
    return [p for _, p in scored]


def _clear_chat_session():
    """Clear conversational history and state while preserving shopping cart."""
    session["conversation"] = []
    session["active_conversation_id"] = None
    session["pending_item"] = None
    session["awaiting_confirmation"] = False
    session["awaiting_quote_confirmation"] = False
    session["awaiting_preferences"] = False
    session["consulting_category"] = None
    session["consulting_qty"] = 1
    session["last_message"] = ""
    session["last_intent"] = "general"
    session["last_products"] = []
    session["last_suggestions"] = []


@app.route("/", methods=["GET"])
def index():
    _get_session_cart()

    manual_query = request.args.get("q", "").strip()
    # If the user refreshes or visits the home page without an active filter query, clear chats
    if not manual_query:
        _clear_chat_session()

    products = _search_catalog(manual_query)
    product_chunks = [products[i:i + 3] for i in range(0, len(products), 3)]
    last_message = session.get("last_message", "")
    last_intent = session.get("last_intent", "general")
    last_products = session.get("last_products", [])
    last_suggestions = session.get("last_suggestions", [])
    conversation = session.get("conversation", [])
    return render_template(
        "index.html",
        products=products,
        product_chunks=product_chunks,
        manual_query=manual_query,
        last_message=last_message,
        last_intent=last_intent,
        last_products=last_products,
        last_suggestions=last_suggestions,
        conversation=conversation,
    )


@app.route("/clear-chat", methods=["GET", "POST"])
def clear_chat():
    _clear_chat_session()
    return redirect(url_for("index"))


@app.route("/search", methods=["GET"])
def search_products():
    return redirect(url_for("index", q=request.args.get("q", "").strip()))


def handle_conversational_step(message: str) -> Tuple[str, str, List[str], List[Dict]]:
    """Conversational step handler powered by QwenBot with full multi-turn context memory."""
    return qwen_bot.handle_step(
        message=message,
        session=session,
        db=db,
        pdf_generator=pdf_generator,
        search_catalog_fn=_search_catalog,
        recommend_fn=_recommend_product,
        calculate_summary_fn=_calculate_summary,
        cart_products_fn=_cart_products,
        clear_cart_fn=_clear_session_cart,
        generate_pdf_fn=_generate_quotation_pdf,
        categories_dict=CATEGORIES,
        consultation_dict=CATEGORY_CONSULTATION,
    )


@app.route("/ai-search", methods=["GET", "POST"])
def ai_search():
    if request.method == "GET":
        _clear_chat_session()
        return redirect(url_for("index"))

    _get_session_cart()
    message = request.form.get("message", "").strip()
    if not message:
        return redirect(url_for("index"))

    try:
        conversation_id = session.get("active_conversation_id")
        if not conversation_id:
            conversation_id = f"CONV-{uuid.uuid4().hex[:12].upper()}"
            session["active_conversation_id"] = conversation_id

        reply, intent, last_prods, last_suggs = handle_conversational_step(message)

        db.save_conversation_message(conversation_id, "user", message)
        db.save_conversation_message(conversation_id, "assistant", reply)

        conversation_history = db.get_conversation_history(conversation_id)
        session["conversation"] = conversation_history

        session["last_products"] = last_prods
        session["last_message"] = message
        session["last_intent"] = intent
        session["last_suggestions"] = last_suggs

        products = _search_catalog("")
        product_chunks = [products[i:i + 3] for i in range(0, len(products), 3)]
        return render_template(
            "index.html",
            products=products,
            product_chunks=product_chunks,
            manual_query="",
            last_message=message,
            last_intent=intent,
            last_products=last_prods,
            last_suggestions=last_suggs,
            conversation=session.get("conversation", []),
        )
    except Exception as exc:
        logger.exception("Error processing AI search: %s", exc)
        session["last_message"] = message
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

    old_conversation_id = session.get("active_conversation_id")
    if old_conversation_id and old_conversation_id.startswith("CONV-"):
        db.move_conversation_to_quotation(old_conversation_id, quotation_id)
        session["active_conversation_id"] = quotation_id

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


@app.route("/api/agent", methods=["POST"])
def api_agent():
    """Direct JSON REST API endpoint for the AI tool-calling agent."""
    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    user_message = payload.get("message", "").strip()
    if not user_message:
        return {"status": "error", "message": "Missing 'message' parameter in request."}, 400

    _get_session_cart()
    conversation_id = session.get("active_conversation_id")
    if not conversation_id:
        conversation_id = f"CONV-{uuid.uuid4().hex[:12].upper()}"
        session["active_conversation_id"] = conversation_id

    reply, intent, last_prods, last_suggs = handle_conversational_step(user_message)

    db.save_conversation_message(conversation_id, "user", user_message)
    db.save_conversation_message(conversation_id, "assistant", reply)

    cart_items = _cart_products()
    summary = _calculate_summary(cart_items)

    return {
        "status": "success",
        "reply": reply,
        "intent": intent,
        "history": db.get_conversation_history(conversation_id),
        "cart": [
            {
                "product_id": item["product"].id,
                "name": item["product"].name,
                "price": item["product"].price,
                "quantity": item["quantity"],
            }
            for item in cart_items
        ],
        "summary": summary,
        "quotation_id": session.get("quotation_id"),
        "quotation_pdf": session.get("quotation_pdf"),
        "download_url": url_for("download_pdf", filename=session.get("quotation_pdf")) if session.get("quotation_pdf") else None,
    }


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=False)
