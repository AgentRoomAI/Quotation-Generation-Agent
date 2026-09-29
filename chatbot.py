import re
import logging
from typing import Dict, List, Tuple, Optional, Any

from llm import generate_response, summarize_conversation

logger = logging.getLogger(__name__)


class QuotationChatbot:
    """Extract user intent and product quantities from natural-language requests.

    Modifications:
    - This class now integrates with `llm.generate_response` to get an assistant
      reply for conversational contexts. The business logic (product/pricing lookups)
      remains the responsibility of Python functions in the application.
    - We intentionally keep extraction logic local and deterministic so the LLM
      never invents prices, stock, GST or discounts.
    """

    MAX_CONTEXT_CHARS = 8000
    RECENT_MESSAGES_TO_KEEP = 6

    def __init__(self):
        # Keywords used for lightweight, deterministic intent extraction.
        self.intent_keywords = {
            "request_quote": ["quote", "quotation", "need", "buy", "purchase"],
            "product_query": ["price", "stock", "availability", "available"],
        }

    def extract_intent(self, message: str) -> str:
        """Return one of: 'request_quote', 'product_query', or 'general'."""
        lowered = (message or "").lower()
        if any(keyword in lowered for keyword in self.intent_keywords["request_quote"]):
            return "request_quote"
        if any(keyword in lowered for keyword in self.intent_keywords["product_query"]):
            return "product_query"
        return "general"

    def extract_products(self, message: str) -> List[Tuple[str, int]]:
        """Deterministically extract (product_name, quantity) pairs from the message.

        This function uses deterministic regex-based extraction to ensure the
        application has precise product names/quantities to map to database lookups.
        """
        items: List[Tuple[str, int]] = []
        if not message:
            return items

        cleaned = re.sub(r"\b(i|need|please|want|buy|purchase|for|the|a|an)\b", " ", message.lower())
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if not cleaned:
            return items

        parts = re.split(r"\b(?:and|or|,|;|plus)\b", cleaned)
        for part in parts:
            part = part.strip()
            if not part:
                continue

            match = re.match(r"(\d+)\s*(?:x|times)?\s*([a-zA-Z0-9\-\_/&]+(?:\s+[a-zA-Z0-9\-\_/&]+)*)", part)
            if match:
                quantity = int(match.group(1))
                product_name = match.group(2).strip()
                if product_name:
                    items.append((product_name, quantity))

        return items

    def parse_message(self, message: str) -> Dict[str, object]:
        """Return a small parsed structure with intent and extracted products."""
        return {
            "intent": self.extract_intent(message),
            "products": self.extract_products(message),
            "message": message,
        }

    @staticmethod
    def calculate_context_size(conversation_history: Optional[List[Dict[str, str]]], existing_summary: str = "") -> int:
        history_text = "\n".join(
            f"{item.get('role', 'user')}: {item.get('content', '')}"
            for item in conversation_history or []
        )
        return len((existing_summary or "") + history_text)

    def _build_context_for_prompt(self, user_message: str, conversation_history: Optional[List[Dict[str, str]]], existing_summary: str = "") -> str:
        history = conversation_history or []
        summary_text = (existing_summary or "").strip()
        messages_text = "\n".join(
            f"{item.get('role', 'user')}: {item.get('content', '')}"
            for item in history
        )
        context = ""
        if summary_text:
            context += f"Previous conversation summary:\n{summary_text}\n\n"
        if messages_text:
            context += f"Conversation history:\n{messages_text}\n\n"
        context += f"Current user message:\n{user_message}\n"
        return context.strip()

    def get_llm_response(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        existing_summary: str = "",
        context_factory: Optional[Any] = None,
    ) -> Dict[str, object]:
        """Return a structured assistant reply and summary state for the current quotation."""
        conversation_history = conversation_history or []
        existing_summary = existing_summary or ""

        try:
            logger.debug("Requesting LLM response for message: %s", user_message)
            context_size = self.calculate_context_size(conversation_history, existing_summary)
            was_compressed = False
            summary_text = existing_summary.strip()

            if context_size >= self.MAX_CONTEXT_CHARS:
                older_messages = conversation_history[:-self.RECENT_MESSAGES_TO_KEEP] if len(conversation_history) > self.RECENT_MESSAGES_TO_KEEP else []
                recent_messages = conversation_history[-self.RECENT_MESSAGES_TO_KEEP:] if conversation_history else []
                if older_messages or summary_text:
                    new_summary = summarize_conversation(older_messages, summary_text)
                    if summary_text and new_summary and new_summary.strip() != summary_text.strip():
                        summary_text = f"{summary_text.strip()}\n{new_summary.strip()}"
                    elif new_summary:
                        summary_text = new_summary.strip()
                    was_compressed = True
                prompt_context = self._build_context_for_prompt(
                    user_message,
                    recent_messages,
                    summary_text,
                )
                reply = generate_response(prompt_context, [], context_factory=context_factory)
            else:
                prompt_context = self._build_context_for_prompt(user_message, conversation_history, existing_summary)
                reply = generate_response(prompt_context, [], context_factory=context_factory)

            logger.debug("LLM replied with %d chars", len(str(reply)))
            return {
                "reply": str(reply).strip() or "I'm sorry — I couldn't process that right now.",
                "updated_summary": summary_text,
                "was_compressed": was_compressed,
            }
        except Exception as exc:
            logger.exception("LLM call failed: %s", exc)
            return {
                "reply": "I'm sorry — I couldn't process that right now.",
                "updated_summary": existing_summary,
                "was_compressed": False,
            }

