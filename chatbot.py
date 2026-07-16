import re
from typing import Dict, List, Tuple


class QuotationChatbot:
    """Extract user intent and product quantities from natural-language requests."""

    def __init__(self):
        self.intent_keywords = {
            "request_quote": ["quote", "quotation", "need", "buy", "purchase"],
            "product_query": ["price", "stock", "availability", "available"],
        }

    def extract_intent(self, message: str) -> str:
        lowered = message.lower()
        if any(keyword in lowered for keyword in self.intent_keywords["request_quote"]):
            return "request_quote"
        if any(keyword in lowered for keyword in self.intent_keywords["product_query"]):
            return "product_query"
        return "general"

    def extract_products(self, message: str) -> List[Tuple[str, int]]:
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

            match = re.match(r"(\d+)\s*(?:x|times)?\s*([a-zA-Z0-9\-/&]+(?:\s+[a-zA-Z0-9\-/&]+)*)", part)
            if match:
                quantity = int(match.group(1))
                product_name = match.group(2).strip()
                if product_name:
                    items.append((product_name, quantity))

        return items

    def parse_message(self, message: str) -> Dict[str, object]:
        return {
            "intent": self.extract_intent(message),
            "products": self.extract_products(message),
            "message": message,
        }
