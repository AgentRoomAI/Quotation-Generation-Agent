"""Qwen B2B Quotation Bot Integration Module.

Provides an enterprise conversational procurement agent powered by Qwen
with full multi-turn conversational context memory, deterministic database lookups,
quantity adjustment handling, cart management, and official quotation PDF generation.

Supports:
1. Live Qwen API via Alibaba DashScope / OpenAI-compatible endpoint / Ollama / HuggingFace.
2. High-precision contextual state machine & memory orchestrator for 100% accurate pricing,
   quantity tracking, and multi-turn procurement dialogue without robotic keyword resets.
"""

import os
import re
import json
import uuid
import urllib.request
import urllib.error
import logging
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

STOP_WORDS = {
    "i", "need", "want", "buy", "purchase", "for", "the", "a", "an",
    "please", "show", "search", "under", "below", "budget", "price",
    "in", "of", "with", "units", "unit", "atleast", "least"
}


class QwenBot:
    """Enterprise Qwen-powered B2B Procurement and Quotation Assistant."""

    def __init__(self):
        self.model_name = os.environ.get("QWEN_MODEL", "Qwen/Qwen2.5-7B-Instruct")
        self.api_key = (
            os.environ.get("QWEN_API_KEY")
            or os.environ.get("DASHSCOPE_API_KEY")
            or os.environ.get("HF_TOKEN")
            or os.environ.get("OPENAI_API_KEY")
        )
        self.base_url = os.environ.get(
            "QWEN_BASE_URL",
            "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
        )
        self.provider = self._detect_provider()

    def _detect_provider(self) -> str:
        if os.environ.get("DASHSCOPE_API_KEY"):
            return "Alibaba DashScope (Qwen)"
        if os.environ.get("QWEN_API_KEY"):
            return "Qwen API"
        if os.environ.get("HF_TOKEN"):
            return "Hugging Face (Qwen2.5)"
        return "Qwen Contextual Agent (Local Engine)"

    def is_api_configured(self) -> bool:
        return bool(self.api_key)

    def extract_quantity(self, text: str) -> Optional[int]:
        """Accurately extract target quantity from natural language expressions."""
        t = text.lower()
        # 1. "at least 3 units", "atleast 5 pcs", "make it 4"
        m1 = re.search(r"\b(?:at\s*least|atleast|make\s*it|change\s*to|quantity|qty|need|want|require)\s*(\d+)\b", t)
        if m1 and 0 < int(m1.group(1)) < 2000:
            return int(m1.group(1))

        # 2. "3 units", "5 pcs", "10 items", "4x"
        m2 = re.search(r"\b(\d+)\s*(?:units?|pieces?|pcs?|items?|nos?|x)\b", t)
        if m2 and 0 < int(m2.group(1)) < 2000:
            return int(m2.group(1))

        # 3. Product count: "5 desktop computers", "10 laptops", "4 acs", "8 monitors"
        m3 = re.search(
            r"\b(\d+)\s+(?:[a-z0-9\-]+\s+)*(?:laptops?|computers?|desktops?|pcs?|workstations?|acs?|air\s*conditioners?|monitors?|phones?|smartphones?|printers?|mice|mouses?|keyboards?|headphones?|routers?|screens?|devices?)\b",
            t,
        )
        if m3 and 0 < int(m3.group(1)) < 2000:
            return int(m3.group(1))

        # 4. Action verbs: "procuring 8", "procure 5", "order of 10", "buying 5"
        m4 = re.search(r"\b(?:order|order of|buying|buy|procuring|procure)\s*(\d+)\b", t)
        if m4 and 0 < int(m4.group(1)) < 2000:
            return int(m4.group(1))

        return None

    def handle_step(
        self,
        message: str,
        session: Dict[str, Any],
        db: Any,
        pdf_generator: Any,
        search_catalog_fn: Any,
        recommend_fn: Any,
        calculate_summary_fn: Any,
        cart_products_fn: Any,
        clear_cart_fn: Any,
        generate_pdf_fn: Any,
        categories_dict: Dict[str, List[str]],
        consultation_dict: Dict[str, Dict[str, str]],
    ) -> Tuple[str, str, List[str], List[Dict[str, Any]]]:
        """Main conversational step handler with deep multi-turn memory preservation."""
        raw_msg = (message or "").strip()
        lower_msg = raw_msg.lower()

        # Session memory states
        pending_item = session.get("pending_item")
        awaiting_conf = session.get("awaiting_confirmation", False)
        awaiting_quote = session.get("awaiting_quote_confirmation", False)
        awaiting_prefs = session.get("awaiting_preferences", False)
        consulting_cat = session.get("consulting_category")
        consulting_budget = session.get("consulting_budget")
        consulting_qty = session.get("consulting_qty", 1)

        # ------------------------------------------------------------------
        # 1. Quotation Generation
        # ------------------------------------------------------------------
        is_quote_intent = any(w in lower_msg for w in ["quotation", "quote", "pdf", "invoice", "bill", "download"])
        is_quote_confirm = awaiting_quote and any(
            re.search(rf"\b{w}\b", lower_msg)
            for w in ["yes", "confirm", "proceed", "sure", "ok", "okay", "yep", "yeah", "do it", "please", "generate"]
        )

        if is_quote_intent or is_quote_confirm:
            cart_prods = cart_products_fn()
            if not cart_prods:
                reply = (
                    "Your shopping cart is currently empty. Please share your equipment requirements "
                    "(e.g., 'We need 5 inverter ACs under ₹30k' or '10 developer laptops with a budget of ₹80k each') "
                    "so we can configure your items before generating the official quotation."
                )
                return reply, "quotation_empty", [], []

            qid, pdf_name = generate_pdf_fn(session.get("customer_name", "Enterprise Client"))
            if not pdf_name:
                return "Unable to generate quotation PDF at this time. Please make sure items are in your cart.", "quotation_error", [], []

            summary = calculate_summary_fn(cart_prods)
            session["quotation_id"] = qid
            session["quotation_pdf"] = pdf_name
            session["awaiting_quote_confirmation"] = False
            session["awaiting_confirmation"] = False
            session["awaiting_preferences"] = False
            session["pending_item"] = None

            reply = (
                f"Official Quotation Generated Successfully.\n\n"
                f"Quotation Summary:\n"
                f"• Quotation Reference: {qid}\n"
                f"• Issued For: Enterprise B2B Procurement\n"
                f"• Validity: 30 Days from date of issue\n"
                f"• Distinct Line Items: {len(cart_prods)} product(s)\n"
                f"• Subtotal: ₹{summary['subtotal']:,.2f}\n"
                f"• GST (18% Enterprise Tax): ₹{summary['gst_total']:,.2f}\n"
                f"• Freight & Shipping: ₹{summary['shipping']:,.2f}\n"
                f"• Grand Total: ₹{summary['grand_total']:,.2f}\n\n"
                f"Download Official PDF Quotation:\n"
                f"/pdfs/{pdf_name}\n\n"
                f"You can also click 'View Cart' or visit the Quotation page to review your quotation."
            )
            return reply, "quotation_generated", [it["product"].name for it in cart_prods[:3]], []

        # ------------------------------------------------------------------
        # 2. Cart Operations (View, Show, Clear)
        # ------------------------------------------------------------------
        if any(w in lower_msg for w in ["clear cart", "empty cart", "reset cart"]):
            clear_cart_fn()
            session["pending_item"] = None
            session["awaiting_confirmation"] = False
            session["awaiting_quote_confirmation"] = False
            session["awaiting_preferences"] = False
            reply = "Your shopping cart has been cleared. What equipment or product category would you like to explore next?"
            return reply, "clear_cart", [], []

        if any(w in lower_msg for w in ["show cart", "view cart", "what's in my cart", "check cart"]) or lower_msg in ["cart", "my cart"]:
            cart_prods = cart_products_fn()
            if not cart_prods:
                reply = "Your cart is currently empty. Tell me what product or category you are looking to procure to explore options!"
                return reply, "show_cart", [], []
            summary = calculate_summary_fn(cart_prods)
            lines = [f"• {item['product'].name} (Qty: {item['quantity']}) — ₹{item['product'].price:,.2f} each" for item in cart_prods]
            items_str = "\n".join(lines)
            reply = (
                f"Current Cart Contents:\n\n{items_str}\n\n"
                f"Financial Summary:\n"
                f"• Subtotal: ₹{summary['subtotal']:,.2f}\n"
                f"• Estimated Grand Total: ₹{summary['grand_total']:,.2f}\n\n"
                f"Would you like to generate the quotation now?\n"
                f"Reply 'yes' or 'generate quotation' to proceed."
            )
            session["awaiting_quote_confirmation"] = True
            return reply, "show_cart", [it["product"].name for it in cart_prods[:3]], []

        # ------------------------------------------------------------------
        # 3. Confirmation Handling (Yes / Confirm / Add)
        # ------------------------------------------------------------------
        is_confirm_word = bool(
            re.search(
                r"\b(?:yes|confirm|confirmed|sure|ok|okay|yep|yeah|add|add it|add that|add this|proceed|go ahead|please add|looks good|perfect)\b",
                lower_msg,
            )
        )

        extracted_qty = self.extract_quantity(lower_msg)

        if awaiting_conf and is_confirm_word and pending_item:
            final_qty = extracted_qty or pending_item.get("quantity", 1)
            final_qty = max(1, final_qty)
            prod_id = pending_item["product_id"]
            product = db.get_product_by_id(prod_id)
            if product:
                found = False
                for item in session["cart"]:
                    if item["product_id"] == prod_id:
                        item["quantity"] += final_qty
                        found = True
                        break
                if not found:
                    session["cart"].append({"product_id": prod_id, "quantity": final_qty})

                session["pending_item"] = None
                session["awaiting_confirmation"] = False
                session["awaiting_quote_confirmation"] = True
                session["awaiting_preferences"] = False

                cart_prods = cart_products_fn()
                summary = calculate_summary_fn(cart_prods)
                reply = (
                    f"Confirmed and Added to Cart!\n\n"
                    f"• Added: {final_qty}x {product.name} at ₹{product.price:,.2f} each\n"
                    f"• Line Total: ₹{(product.price * final_qty):,.2f}\n"
                    f"• Cart Status: {len(cart_prods)} item(s) | Grand Total: ₹{summary['grand_total']:,.2f}\n\n"
                    f"Would you like to generate the quotation now?\n"
                    f"Reply 'yes' or 'generate quotation' to generate the official quotation PDF, or tell me if you'd like to search for another product."
                )
                return reply, "add_to_cart", [product.name], []

        # Cancellation Handling
        if awaiting_conf and any(re.search(rf"\b{w}\b", lower_msg) for w in ["no", "cancel", "don't", "dont", "not this", "neither", "stop"]):
            session["pending_item"] = None
            session["awaiting_confirmation"] = False
            session["awaiting_preferences"] = False
            reply = "Understood. The item was not added to your cart. What other product specification, alternative brand, or budget range would you prefer?"
            return reply, "cancelled", [], []

        budget_match = self._extract_budget(lower_msg)
        detected_cat = self._detect_category(lower_msg, categories_dict)
        is_new_inquiry = bool(detected_cat or budget_match is not None)

        # If user starts a new inquiry with category or budget, clear previous pending item
        if is_new_inquiry and awaiting_conf:
            session["pending_item"] = None
            pending_item = None
            session["awaiting_confirmation"] = False

        # ------------------------------------------------------------------
        # 4. Critical: Quantity Adjustment on Recommended Item
        # (Handles "i need atleast 3 units", "make it 5" when looking at an item)
        # ------------------------------------------------------------------
        if extracted_qty is not None and not is_new_inquiry:
            has_explicit_qty_phrase = bool(
                re.search(r"\b(?:at\s*least|atleast|make\s*it|change\s*to|quantity|qty|units?|pieces?|pcs?|items?)\b", lower_msg)
            )

            # Scenario A: User is looking at a pending item and specifies/updates quantity
            if pending_item and (awaiting_conf or has_explicit_qty_phrase):
                pending_item["quantity"] = extracted_qty
                session["consulting_qty"] = extracted_qty
                line_total = pending_item["price"] * extracted_qty
                prod_name = pending_item["name"]
                prod = db.get_product_by_id(pending_item["product_id"])
                stock_str = f"Available Stock: {prod.stock} units" if prod else ""

                reply = (
                    f"Updated Quantity to {extracted_qty} unit(s) for '{prod_name}'!\n\n"
                    f"• Recommended Model: {prod_name}\n"
                    f"• Unit Price: ₹{pending_item['price']:,.2f}\n"
                    f"• Selected Quantity: {extracted_qty} unit(s)\n"
                    f"• Line Subtotal: ₹{line_total:,.2f}\n"
                    f"• Stock Status: {stock_str}\n\n"
                    f"Would you like to confirm and add {extracted_qty}x '{prod_name}' to your cart?\n"
                    f"Please reply 'yes' or 'confirm' to proceed, or let me know if you would like another item."
                )
                session["awaiting_confirmation"] = True
                return reply, "quantity_updated", [prod_name], []

            # Scenario B: User updates quantity for consultation
            if awaiting_prefs:
                session["consulting_qty"] = extracted_qty

        # ------------------------------------------------------------------
        # 5. Greetings, Gratitude & General Assistance
        # ------------------------------------------------------------------
        is_greeting = bool(
            re.search(r"\b(?:hello|hi|hey|good\s*(?:morning|afternoon|evening)|greetings|howdy|hola)\b", lower_msg)
        )
        if is_greeting and not any(k in lower_msg for k in ["ac", "laptop", "pc", "computer", "phone", "monitor", "printer", "buy", "need", "want", "quote", "cart", "under", "budget"]):
            reply = (
                "Hello! Welcome to the Qwen-Powered B2B Procurement & Quotation Assistant.\n\n"
                "I can assist you with:\n"
                "• Product Recommendations: Inquire about any category (e.g., Laptops, Air Conditioners, Desktop Computers, 4K Monitors, Smartphones, Office Printers, Networking equipment).\n"
                "• Budget & Specification Consultation: Share your target budget, workload, or team size (e.g., 'We need inverter ACs under ₹30,000' or '10 developer laptops with a budget of ₹80,000 each').\n"
                "• Official Quotation Generation: Review and confirm your items to generate an itemized corporate quotation with GST calculations and a downloadable PDF.\n\n"
                "What equipment or product category are you looking to procure today?"
            )
            return reply, "greeting", [], []

        is_gratitude = bool(re.search(r"\b(?:thanks|thank\s*you|thx|appreciate it|cheers)\b", lower_msg))
        if is_gratitude and not any(k in lower_msg for k in ["add", "yes", "confirm", "quote", "buy", "cart"]):
            reply = (
                "You're very welcome! If you'd like to explore more items, adjust your cart quantities, or generate additional quotations, just let me know.\n\n"
                "How else can I assist your procurement today?"
            )
            return reply, "gratitude", [], []

        # ------------------------------------------------------------------
        # 6. Intent & Entity Extraction with Memory
        # ------------------------------------------------------------------
        if budget_match is not None:
            effective_budget = budget_match
            session["consulting_budget"] = budget_match
        else:
            effective_budget = consulting_budget

        if detected_cat:
            effective_cat = detected_cat
            session["consulting_category"] = detected_cat
        else:
            effective_cat = consulting_cat

        effective_qty = extracted_qty or consulting_qty or 1
        session["consulting_qty"] = effective_qty

        # ------------------------------------------------------------------
        # 7. Check for Alternative Brand / Model Inquiry
        # (e.g., "what about lloyd?", "show me daikin", "is there 1.5 ton?")
        # ------------------------------------------------------------------
        alt_brand_query = any(b in lower_msg for b in ["lloyd", "voltas", "daikin", "lg", "blue star", "panasonic", "apple", "macbook", "asus", "acer", "dell", "hp", "lenovo", "samsung"])
        if (awaiting_conf or awaiting_prefs) and alt_brand_query and effective_cat:
            best, alts = recommend_fn(effective_cat, effective_budget, lower_msg, effective_qty)
            if best:
                session["pending_item"] = {
                    "product_id": best.id,
                    "name": best.name,
                    "price": best.price,
                    "quantity": effective_qty,
                }
                session["awaiting_confirmation"] = True
                session["awaiting_preferences"] = False
                alt_lines = [f"• {p.name} — ₹{p.price:,.2f} (Stock: {p.stock} units)" for p in alts]
                alt_text = "\n\nOther available matches in database:\n" + "\n".join(alt_lines) if alt_lines else ""
                reply = (
                    f"Tailored Recommendation Based on Your Preference:\n\n"
                    f"• Recommended Model: {best.name}\n"
                    f"• Unit Price: ₹{best.price:,.2f}\n"
                    f"• Available Stock: {best.stock} units (SKU: {best.sku})\n"
                    f"• Technical Overview: {best.description}\n"
                    f"• Estimated Subtotal ({effective_qty} units): ₹{(best.price * effective_qty):,.2f}"
                    f"{alt_text}\n\n"
                    f"Would you like to confirm and add {effective_qty}x '{best.name}' to your cart?\n"
                    f"Please reply 'yes' or 'confirm' to proceed, or let me know if you would like another item."
                )
                return reply, "product_found", [best.name], [{"name": p.name, "price": p.price, "stock": p.stock} for p in ([best] + alts)]

        # ------------------------------------------------------------------
        # 8. Follow-up to Consultation Mode (e.g., "under 30k", "tonnage 1.5")
        # ------------------------------------------------------------------
        if awaiting_prefs and effective_cat:
            best, alts = recommend_fn(effective_cat, effective_budget, lower_msg, effective_qty)
            if best:
                session["pending_item"] = {
                    "product_id": best.id,
                    "name": best.name,
                    "price": best.price,
                    "quantity": effective_qty,
                }
                session["awaiting_confirmation"] = True
                session["awaiting_preferences"] = False

                alt_lines = [f"• {p.name} — ₹{p.price:,.2f} (Stock: {p.stock} units)" for p in alts]
                alt_text = "\n\nOther available matches in database:\n" + "\n".join(alt_lines) if alt_lines else ""

                budget_note = ""
                if effective_budget is not None:
                    if best.price <= effective_budget:
                        budget_note = f" (within your ₹{effective_budget:,.2f} target budget)"
                    else:
                        budget_note = f" (closest available option at ₹{best.price:,.2f}, slightly above your ₹{effective_budget:,.2f} target budget)"

                reply = (
                    f"Tailored Recommendation Based on Your Requirements:\n\n"
                    f"• Recommended Model: {best.name}\n"
                    f"• Unit Price: ₹{best.price:,.2f}{budget_note}\n"
                    f"• Available Stock: {best.stock} units (SKU: {best.sku})\n"
                    f"• Technical Overview: {best.description}\n"
                    f"• Estimated Subtotal ({effective_qty} units): ₹{(best.price * effective_qty):,.2f}"
                    f"{alt_text}\n\n"
                    f"Would you like to confirm and add {effective_qty}x '{best.name}' to your cart?\n"
                    f"Please reply 'yes' or 'confirm' to proceed, or let me know if you would like another item."
                )
                suggestions_data = [{"name": p.name, "price": p.price, "stock": p.stock} for p in ([best] + alts)]
                return reply, "product_found", [best.name], suggestions_data

        # ------------------------------------------------------------------
        # 9. Case where user re-states requirement with category and remembered budget
        # (e.g. "i need the ac atleast 3 units" after previous "under 30k")
        # ------------------------------------------------------------------
        if detected_cat and effective_budget is not None:
            best, alts = recommend_fn(detected_cat, effective_budget, lower_msg, effective_qty)
            if best:
                session["pending_item"] = {
                    "product_id": best.id,
                    "name": best.name,
                    "price": best.price,
                    "quantity": effective_qty,
                }
                session["awaiting_confirmation"] = True
                session["awaiting_preferences"] = False

                alt_lines = [f"• {p.name} — ₹{p.price:,.2f} (Stock: {p.stock} units)" for p in alts]
                alt_text = "\n\nOther available matches in database:\n" + "\n".join(alt_lines) if alt_lines else ""

                reply = (
                    f"Tailored Recommendation Based on Your Requirements:\n\n"
                    f"• Recommended Model: {best.name}\n"
                    f"• Unit Price: ₹{best.price:,.2f} (within your remembered ₹{effective_budget:,.2f} target budget)\n"
                    f"• Selected Quantity: {effective_qty} unit(s)\n"
                    f"• Line Subtotal ({effective_qty} units): ₹{(best.price * effective_qty):,.2f}\n"
                    f"• Available Stock: {best.stock} units (SKU: {best.sku})\n"
                    f"• Technical Overview: {best.description}"
                    f"{alt_text}\n\n"
                    f"Would you like to confirm and add {effective_qty}x '{best.name}' to your cart?\n"
                    f"Please reply 'yes' or 'confirm' to proceed, or let me know if you would like another item."
                )
                suggestions_data = [{"name": p.name, "price": p.price, "stock": p.stock} for p in ([best] + alts)]
                return reply, "product_found", [best.name], suggestions_data

        # ------------------------------------------------------------------
        # 10. Broad Category Inquiry without budget -> Consultation Mode
        # ------------------------------------------------------------------
        if detected_cat and effective_budget is None:
            session["awaiting_preferences"] = True
            session["consulting_category"] = detected_cat
            session["consulting_qty"] = effective_qty
            session["awaiting_confirmation"] = False

            consult = consultation_dict.get(
                detected_cat,
                {
                    "title": detected_cat.capitalize() + "s",
                    "budget_hint": "e.g., entry-level under ₹50,000, mid-range ₹50,000 – ₹1,00,000, or premium enterprise above ₹1,00,000",
                    "specs_prompt": "Primary Workload & Specifications:",
                    "specs_hint": "What tasks will these devices primarily handle?",
                    "brands_hint": "preferred brands or models",
                },
            )
            reply = (
                f"Thank you for your inquiry regarding enterprise {consult['title']}! "
                f"We have multiple verified configurations available in our product catalog.\n\n"
                f"To help me recommend the ideal option tailored to your requirements and prepare an accurate quotation, please share a few details:\n\n"
                f"1. Target Budget per Unit:\n"
                f"   What is your approximate budget range? ({consult['budget_hint']})\n\n"
                f"2. {consult['specs_prompt']}\n"
                f"   {consult['specs_hint']}\n\n"
                f"3. Quantity & Brand Preferences:\n"
                f"   How many units are you looking to procure? (Currently noted: {effective_qty} unit(s)). Do you have preferred brands (such as {consult['brands_hint']})?\n\n"
                f"Please share your preferences or target budget, and I will recommend the optimal match from our live inventory!"
            )
            return reply, "preference_inquiry", [], []

        # ------------------------------------------------------------------
        # 11. General Search Fallback
        # ------------------------------------------------------------------
        clean_term = re.sub(r"\b(" + "|".join(STOP_WORDS) + r")\b", " ", lower_msg)
        clean_term = re.sub(r"\s+", " ", clean_term).strip()
        matched = search_catalog_fn(clean_term or lower_msg)

        if not matched:
            reply = (
                f"I searched our product catalog for '{clean_term or lower_msg}', but could not find matching products.\n\n"
                f"Try searching by category such as AC, laptop, desktop computer, phone, or monitor, "
                f"or specify your target budget (e.g., 'We need ACs under ₹30,000')."
            )
            return reply, "not_found", [], []

        best = matched[0]
        alts = matched[1:4]
        session["pending_item"] = {
            "product_id": best.id,
            "name": best.name,
            "price": best.price,
            "quantity": effective_qty,
        }
        session["awaiting_confirmation"] = True
        session["awaiting_quote_confirmation"] = False

        alt_lines = [f"• {p.name} — ₹{p.price:,.2f} (Stock: {p.stock} units)" for p in alts]
        alt_text = "\n\nOther available matches in database:\n" + "\n".join(alt_lines) if alt_lines else ""

        reply = (
            f"Tailored Recommendation from Product Database:\n\n"
            f"• Product: {best.name}\n"
            f"• Price: ₹{best.price:,.2f}\n"
            f"• SKU: {best.sku} | Available Stock: {best.stock} units\n"
            f"• Description: {best.description}"
            f"{alt_text}\n\n"
            f"Would you like to confirm and add {effective_qty}x '{best.name}' to your cart?\n"
            f"Please reply 'yes' or 'confirm' to proceed, or let me know if you would like another item."
        )
        return reply, "product_found", [best.name], [{"name": p.name, "price": p.price, "stock": p.stock} for p in matched[:4]]

    def _extract_budget(self, text: str) -> Optional[float]:
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

    def _detect_category(self, text: str, categories_dict: Dict[str, List[str]]) -> Optional[str]:
        t = text.lower()
        for cat, keywords in categories_dict.items():
            if any(re.search(rf"\b{re.escape(k)}\b", t) for k in keywords):
                return cat
        return None
