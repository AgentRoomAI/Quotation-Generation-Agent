"""
Lightweight LLM integration module.

This module now provides two layers:
1. A simple local-model text generator for compatibility.
2. An agent-style tool-calling interface built on top of the same model.

The agent loop is intentionally modular and can operate with either a native
tool-calling capable model or a manual JSON-based tool-call parser.
"""
import importlib.util
import json
import logging
import os
import threading
from typing import Any, Dict, List, Optional

try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    HAS_TORCH = True
except Exception:
    torch = None
    AutoModelForCausalLM = None
    AutoTokenizer = None
    HAS_TORCH = False

from agent import QuotationAgent
from tools import ToolContext

logger = logging.getLogger(__name__)

# Globals populated by lazy loader
TOKENIZER = None
MODEL = None
_MODEL_LOAD_FAILED = False
_MODEL_LOAD_LOCK = threading.Lock()

SUPPORTED_INTENTS = {
    "quotation",
    "add_product",
    "remove_product",
    "update_quantity",
    "show_cart",
    "generate_pdf",
    "help",
    "greeting",
    "unknown",
}


class HuggingFaceToolLLM:
    """A small adapter that exposes a generate(messages, tools) call for the agent."""

    def generate(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        _load_model_once()
        if MODEL is None or TOKENIZER is None:
            return self._heuristic_generate(messages, tools)

        prompt_messages = list(messages)
        if tools:
            prompt_messages.append({
                "role": "system",
                "content": "You are a helpful shopping assistant. Use the available tools when they are necessary. Respond with a JSON object containing either a 'tool_calls' array or a final assistant 'content' string.",
            })

        if hasattr(TOKENIZER, "apply_chat_template"):
            prompt = TOKENIZER.apply_chat_template(prompt_messages, tokenize=False, add_generation_prompt=True)
        else:
            prompt = json.dumps(prompt_messages, ensure_ascii=False)

        inputs = TOKENIZER(prompt, return_tensors="pt")
        model_device = _get_model_device()
        inputs = {k: v.to(model_device) for k, v in inputs.items()}

        generation_config = dict(max_new_tokens=256, do_sample=False)
        with torch.no_grad():
            outputs = MODEL.generate(**inputs, **generation_config)

        decoded = TOKENIZER.decode(outputs[0], skip_special_tokens=True)
        assistant_text = decoded.split("Assistant:")[-1].strip() if "Assistant:" in decoded else decoded[len(prompt):].strip()

        try:
            parsed = json.loads(assistant_text)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

        return {"content": assistant_text or "I can help with that."}

    def _heuristic_generate(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Heuristic fallback when the neural model is not active or during offline operation."""
        if not messages:
            return {"content": "Hello! How can I assist you with products and quotations today?"}

        last_msg = messages[-1]
        role = last_msg.get("role")

        if role == "tool":
            tool_name = last_msg.get("name", "")
            raw_content = last_msg.get("content", "{}")
            try:
                data = json.loads(raw_content)
            except Exception:
                data = {}

            res = data.get("result", {}) if isinstance(data, dict) else {}
            if tool_name == "show_cart":
                items = res.get("items", [])
                summary = res.get("summary", {})
                if not items:
                    return {"content": "Your cart is currently empty. Would you like to search for products?"}
                item_desc = ", ".join(f"{it.get('product_name', 'Item')} (Qty: {it.get('quantity', 1)})" for it in items)
                return {"content": f"Current Cart Contents:\n• {item_desc}\n\nFinancial Summary:\n• Subtotal: ₹{summary.get('subtotal', 0):,.2f}\n• GST (18%): ₹{summary.get('gst_total', 0):,.2f}\n• Grand Total: ₹{summary.get('grand_total', 0):,.2f}"}

            if tool_name == "search_products":
                prods = res.get("products", [])
                if not prods:
                    return {"content": "I searched our product catalog, but no products matched your criteria. Please try searching for a category like laptop, monitor, phone, or printer."}
                best = prods[0]
                alts = prods[1:4]
                alt_str = ""
                if alts:
                    alt_lines = [f"• {p['name']} — ₹{p['price']:,.2f} (Stock: {p['stock']} units)" for p in alts]
                    alt_str = "\n\nOther available matches in database:\n" + "\n".join(alt_lines)
                return {
                    "content": (
                        f"Product Found in Product Database:\n\n"
                        f"• Product: {best['name']}\n"
                        f"• Price: ₹{best['price']:,.2f}\n"
                        f"• SKU: {best['sku']} | Available Stock: {best['stock']} units\n"
                        f"• Description: {best.get('description', '')}"
                        f"{alt_str}\n\n"
                        f"Would you like to confirm and add '{best['name']}' to your cart?\n"
                        f"Please reply 'yes' or 'confirm' to proceed."
                    )
                }

            if tool_name == "add_to_cart":
                return {"content": f"Confirmed and added to cart. Cart currently has {res.get('cart_size', 1)} item(s). You can type 'show cart' or 'generate quotation'."}

            if tool_name == "generate_quotation":
                quote = res.get("quotation")
                if not quote:
                    return {"content": "Your cart is empty. Please add items before generating a quotation."}
                summary = quote.get("summary", {})
                return {"content": f"Official Quotation Calculated:\n• Subtotal: ₹{summary.get('subtotal', 0):,.2f}\n• Tax (GST): ₹{summary.get('gst_total', 0):,.2f}\n• Shipping: ₹{summary.get('shipping', 0):,.2f}\n• Grand Total: ₹{summary.get('grand_total', 0):,.2f}\n\nWould you like to download the official PDF quotation?"}

            if tool_name == "generate_pdf":
                pdf_name = res.get("pdf_name")
                qid = res.get("quotation_id")
                dl = res.get("download_url") or (f"/pdfs/{pdf_name}" if pdf_name else "")
                if pdf_name:
                    return {"content": f"Official Quotation Generated Successfully.\n\nQuotation Details:\n• Reference ID: {qid}\n• Download Link: {dl}"}
                return {"content": res.get("message", "Unable to generate PDF at this time.")}

            if tool_name == "clear_cart":
                return {"content": "Your shopping cart has been cleared."}

            if tool_name == "remove_from_cart":
                return {"content": "The item was removed from your cart."}

            if tool_name == "update_quantity":
                return {"content": res.get("message", "Cart quantity updated.")}

            return {"content": f"Tool {tool_name} completed."}

        # User message fallback
        import re
        text = str(last_msg.get("content", "")).lower().strip()

        if "clear" in text and "cart" in text or text in ["empty cart", "reset cart"]:
            return {"tool_calls": [{"name": "clear_cart", "arguments": {}}]}

        if "pdf" in text or "download" in text:
            return {"tool_calls": [{"name": "generate_pdf", "arguments": {}}]}

        if "quote" in text or "quotation" in text:
            return {"tool_calls": [{"name": "generate_quotation", "arguments": {}}]}

        if "cart" in text and ("show" in text or "view" in text or "what" in text or "check" in text or text == "cart"):
            return {"tool_calls": [{"name": "show_cart", "arguments": {}}]}

        if "add" in text:
            pid_match = re.search(r"(?:product|id)\s*#?\s*(\d+)", text)
            qty_match = re.search(r"(\d+)\s*(?:x|qty|quantity|units?|items?|pieces?)", text)
            qty = int(qty_match.group(1)) if qty_match else 1
            if pid_match:
                return {"tool_calls": [{"name": "add_to_cart", "arguments": {"product_id": int(pid_match.group(1)), "quantity": qty}}]}
            clean_term = re.sub(r"\b(add|to|cart|please|i|want|need|a|an|some)\b", "", text).strip()
            return {"tool_calls": [{"name": "search_products", "arguments": {"category": clean_term or text}}]}

        if any(w in text for w in ["search", "find", "show", "list", "looking for", "price", "laptop", "phone", "monitor", "printer", "watch", "need", "want", "buy"]):
            clean_term = re.sub(r"\b(\d+|search|find|show|list|looking|for|please|a|an|some|i|need|want|buy|purchase|products?)\b", "", text).strip()
            if clean_term.endswith("s") and len(clean_term) > 3 and not clean_term.endswith("ss"):
                clean_term = clean_term[:-1]
            return {"tool_calls": [{"name": "search_products", "arguments": {"category": clean_term or text}}]}

        return {
            "content": "I am your Quotation Generation Assistant. You can ask me to search products, add items to your cart, show your cart, or generate quotation PDFs. How can I help you today?"
        }


def _is_accelerate_available() -> bool:
    return importlib.util.find_spec("accelerate") is not None


def _load_model_once():
    """Load tokenizer and model once for reuse."""
    global TOKENIZER, MODEL, _MODEL_LOAD_FAILED
    with _MODEL_LOAD_LOCK:
        if _MODEL_LOAD_FAILED or (TOKENIZER is not None and MODEL is not None):
            return

        if not HAS_TORCH:
            _MODEL_LOAD_FAILED = True
            return

        model_name = os.environ.get("LLM_MODEL", "Qwen/Qwen3-1.7B")
        hf_token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")
        loader_kwargs = {"trust_remote_code": True}
        if hf_token:
            loader_kwargs["token"] = hf_token
        try:
            cuda_available = torch.cuda.is_available()
            logger.info("Loading model '%s'", model_name)
            TOKENIZER = AutoTokenizer.from_pretrained(model_name, **loader_kwargs)
            if getattr(TOKENIZER, "pad_token", None) is None and getattr(TOKENIZER, "eos_token", None) is not None:
                TOKENIZER.pad_token = TOKENIZER.eos_token

            model_kwargs = dict(loader_kwargs)
            if cuda_available and _is_accelerate_available():
                model_kwargs.update({"device_map": "auto", "torch_dtype": "auto", "low_cpu_mem_usage": True})
            elif _is_accelerate_available():
                model_kwargs.update({"torch_dtype": torch.float16, "low_cpu_mem_usage": True})
            else:
                model_kwargs.update({"torch_dtype": torch.float16})

            MODEL = AutoModelForCausalLM.from_pretrained(model_name, **model_kwargs)
            MODEL.eval()
            logger.info("Loaded model '%s' successfully.", model_name)
        except Exception as exc:  # pragma: no cover - runtime/environment dependent
            logger.exception("Failed to load model '%s': %s", model_name, exc)
            if not hf_token:
                logger.error(
                    "Model '%s' requires Hugging Face authentication. Set HF_TOKEN or HUGGINGFACE_TOKEN and retry.",
                    model_name,
                )
            TOKENIZER = None
            MODEL = None
            _MODEL_LOAD_FAILED = True


def _get_model_device() -> Any:
    if not HAS_TORCH or MODEL is None:
        return "cpu"
    device = getattr(MODEL, "device", None)
    if device is not None:
        return device
    try:
        return next(MODEL.parameters()).device
    except StopIteration:
        return "cpu"


def create_agent(context_factory=None) -> QuotationAgent:
    """Create a configured quotation agent instance."""
    llm_client = HuggingFaceToolLLM()
    return QuotationAgent(llm_client=llm_client, context_factory=context_factory)


def generate_response(
    user_message: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    context_factory: Optional[Any] = None,
) -> str:
    """Compatibility entry point used by the existing chatbot wrapper."""
    try:
        agent = create_agent(context_factory=context_factory or (lambda: ToolContext()))
        agent.history = [{"role": "user", "content": user_message}]
        return agent.run(user_message)
    except Exception as exc:
        logger.exception("Agent generation failed: %s", exc)
        return "I'm sorry — I couldn't process that right now."


def summarize_conversation(old_messages: Optional[List[Dict[str, str]]], existing_summary: str = "") -> str:
    """Create a concise factual memory summary without inventing new details."""
    messages = old_messages or []
    existing_summary = existing_summary or ""

    if not messages and not existing_summary:
        return ""

    summary_prompt = (
        "Return only a concise factual memory summary for this quotation conversation. "
        "Preserve important facts and decisions already made, and do not invent details. "
        "Only include customer requirements, products, quantities, prices, GST/tax information, "
        "discounts, quotation changes, customer preferences, decisions already made, and any pending questions. "
        "Keep it compact and factual.\n\n"
    )
    if existing_summary:
        summary_prompt += f"Existing summary:\n{existing_summary}\n\n"
    if messages:
        summary_prompt += "Older messages:\n"
        for item in messages:
            role = item.get("role", "user")
            content = item.get("content", "")
            summary_prompt += f"{role}: {content}\n"

    try:
        summary = generate_response(summary_prompt, [])
        return str(summary).strip()[:2000]
    except Exception as exc:  # pragma: no cover - runtime dependent
        logger.exception("Conversation summarization failed: %s", exc)
        return existing_summary.strip()
