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
from typing import Any, Dict, List, Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from agent import QuotationAgent
from tools import ToolContext

logger = logging.getLogger(__name__)

# Globals populated by lazy loader
TOKENIZER = None
MODEL = None

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
            return {"content": "The local model is unavailable right now."}

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


def _is_accelerate_available() -> bool:
    return importlib.util.find_spec("accelerate") is not None


def _load_model_once():
    """Load tokenizer and model once for reuse."""
    global TOKENIZER, MODEL
    if TOKENIZER is not None and MODEL is not None:
        return

    model_name = os.environ.get("LLM_MODEL", "Qwen/Qwen3-14B-Instruct")
    try:
        cuda_available = torch.cuda.is_available()
        logger.info("Loading model '%s'", model_name)
        TOKENIZER = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        if getattr(TOKENIZER, "pad_token", None) is None and getattr(TOKENIZER, "eos_token", None) is not None:
            TOKENIZER.pad_token = TOKENIZER.eos_token

        model_kwargs = {"trust_remote_code": True}
        if cuda_available and _is_accelerate_available():
            model_kwargs.update({"device_map": "auto", "torch_dtype": "auto", "low_cpu_mem_usage": True})
        else:
            model_kwargs.update({"torch_dtype": torch.float32})

        MODEL = AutoModelForCausalLM.from_pretrained(model_name, **model_kwargs)
        MODEL.eval()
        logger.info("Loaded model '%s' successfully.", model_name)
    except Exception as exc:  # pragma: no cover - runtime/environment dependent
        logger.exception("Failed to load model '%s': %s", model_name, exc)
        TOKENIZER = None
        MODEL = None


def _get_model_device() -> torch.device:
    if MODEL is None:
        return torch.device("cpu")
    device = getattr(MODEL, "device", None)
    if device is not None:
        return device
    try:
        return next(MODEL.parameters()).device
    except StopIteration:
        return torch.device("cpu")


def create_agent(context_factory=None) -> QuotationAgent:
    """Create a configured quotation agent instance."""
    llm_client = HuggingFaceToolLLM()
    return QuotationAgent(llm_client=llm_client, context_factory=context_factory)


def generate_response(user_message: str, conversation_history: Optional[List[Dict[str, str]]]) -> str:
    """Compatibility entry point used by the existing chatbot wrapper."""
    try:
        agent = create_agent(context_factory=lambda: ToolContext())
        agent.history = [{"role": "user", "content": user_message}]
        return agent.run(user_message)
    except Exception as exc:
        logger.exception("Agent generation failed: %s", exc)
        return "I'm sorry — I couldn't process that right now."
