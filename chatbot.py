import re
<<<<<<< HEAD
from typing import Dict, List, Tuple


class QuotationChatbot:
    """Extract user intent and product quantities from natural-language requests."""

    def __init__(self):
=======
import logging
from typing import Dict, List, Tuple, Optional

from llm import generate_response

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

    def __init__(self):
        # Keywords used for lightweight, deterministic intent extraction.
>>>>>>> bc5e872 (Initial import from local workspace)
        self.intent_keywords = {
            "request_quote": ["quote", "quotation", "need", "buy", "purchase"],
            "product_query": ["price", "stock", "availability", "available"],
        }

    def extract_intent(self, message: str) -> str:
<<<<<<< HEAD
        lowered = message.lower()
=======
        """Return one of: 'request_quote', 'product_query', or 'general'."""
        lowered = (message or "").lower()
>>>>>>> bc5e872 (Initial import from local workspace)
        if any(keyword in lowered for keyword in self.intent_keywords["request_quote"]):
            return "request_quote"
        if any(keyword in lowered for keyword in self.intent_keywords["product_query"]):
            return "product_query"
        return "general"

    def extract_products(self, message: str) -> List[Tuple[str, int]]:
<<<<<<< HEAD
=======
        """Deterministically extract (product_name, quantity) pairs from the message.

        This function uses deterministic regex-based extraction to ensure the
        application has precise product names/quantities to map to database lookups.
        """
>>>>>>> bc5e872 (Initial import from local workspace)
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

<<<<<<< HEAD
            match = re.match(r"(\d+)\s*(?:x|times)?\s*([a-zA-Z0-9\-/&]+(?:\s+[a-zA-Z0-9\-/&]+)*)", part)
=======
            match = re.match(r"(\d+)\s*(?:x|times)?\s*([a-zA-Z0-9\-\_/&]+(?:\s+[a-zA-Z0-9\-\_/&]+)*)", part)
>>>>>>> bc5e872 (Initial import from local workspace)
            if match:
                quantity = int(match.group(1))
                product_name = match.group(2).strip()
                if product_name:
                    items.append((product_name, quantity))

        return items

    def parse_message(self, message: str) -> Dict[str, object]:
<<<<<<< HEAD
=======
        """Return a small parsed structure with intent and extracted products."""
>>>>>>> bc5e872 (Initial import from local workspace)
        return {
            "intent": self.extract_intent(message),
            "products": self.extract_products(message),
            "message": message,
        }
<<<<<<< HEAD
=======

    def get_llm_response(self, user_message: str, conversation_history: Optional[List[Dict[str, str]]]) -> str:
        """Call the LLM generate_response function and return assistant text.

        This wrapper centralizes where the application interacts with the model so
        we can log, handle exceptions, and keep generation behavior consistent.
        """
        try:
            logger.debug("Requesting LLM response for message: %s", user_message)
            reply = generate_response(user_message, conversation_history or [])
            logger.debug("LLM replied with %d chars", len(reply))
            return reply
        except Exception as exc:
            logger.exception("LLM call failed: %s", exc)
            return "I'm sorry — I couldn't process that right now."

>>>>>>> bc5e872 (Initial import from local workspace)
