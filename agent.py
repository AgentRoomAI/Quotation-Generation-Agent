"""Agent loop for tool-calling with a local Hugging Face model."""

import json
import logging
from typing import Any, Callable, Dict, List, Optional

from tool_registry import ToolRegistry, ToolSpec
from tools import ToolContext, add_to_cart, clear_cart, generate_pdf, generate_quotation, remove_from_cart, search_products, show_cart, update_quantity

logger = logging.getLogger(__name__)


class QuotationAgent:
    """A lightweight tool-calling agent for the quotation system.

    The agent keeps a message history, asks the LLM for the next action, executes
    any requested tool calls, feeds the results back into the conversation, and
    continues until the model returns a normal assistant message.
    """

    def __init__(self, llm_client: Any, registry: Optional[ToolRegistry] = None, context_factory: Optional[Callable[[], Any]] = None):
        self.llm_client = llm_client
        self.registry = registry or ToolRegistry()
        if not self.registry.list_tools():
            self._register_default_tools(self.registry)
        self.context_factory = context_factory or (lambda: ToolContext())
        self.history: List[Dict[str, Any]] = []

    def _register_default_tools(self, registry: ToolRegistry) -> None:
        registry.register(ToolSpec(
            name="search_products",
            description="Search the product catalog for products matching a category, filters, or budget.",
            func=search_products,
            parameters={
                "type": "object",
                "properties": {
                    "category": {"type": "string"},
                    "filters": {"type": "object"},
                    "budget": {"type": "number"},
                },
                "required": [],
            },
        ))
        registry.register(ToolSpec(name="add_to_cart", description="Add a product to the session cart.", func=add_to_cart, parameters={
            "type": "object",
            "properties": {"product_id": {"type": "integer"}, "quantity": {"type": "integer"}},
            "required": ["product_id"],
        }))
        registry.register(ToolSpec(name="remove_from_cart", description="Remove a product from the cart.", func=remove_from_cart, parameters={
            "type": "object",
            "properties": {"product_id": {"type": "integer"}},
            "required": ["product_id"],
        }))
        registry.register(ToolSpec(name="update_quantity", description="Update the quantity of a product in the cart.", func=update_quantity, parameters={
            "type": "object",
            "properties": {"product_id": {"type": "integer"}, "quantity": {"type": "integer"}},
            "required": ["product_id", "quantity"],
        }))
        registry.register(ToolSpec(name="show_cart", description="Display the current cart contents.", func=show_cart, parameters={"type": "object", "properties": {}, "required": []}))
        registry.register(ToolSpec(name="generate_quotation", description="Generate a quotation from the current cart.", func=generate_quotation, parameters={"type": "object", "properties": {}, "required": []}))
        registry.register(ToolSpec(name="generate_pdf", description="Create a PDF quotation for the current cart.", func=generate_pdf, parameters={"type": "object", "properties": {}, "required": []}))
        registry.register(ToolSpec(name="clear_cart", description="Clear all items from the shopping cart.", func=clear_cart, parameters={"type": "object", "properties": {}, "required": []}))

    def _build_default_registry(self) -> ToolRegistry:
        registry = ToolRegistry()
        self._register_default_tools(registry)
        return registry

    def run(self, user_message: str) -> str:
        """Run the full agent loop for a user request."""
        context = self.context_factory()
        self.history = [{"role": "user", "content": user_message}]

        for step in range(8):
            response = self.llm_client.generate(self.history, self.registry.to_openai_schema())
            assistant_message = self._normalize_response(response)
            self.history.append({"role": "assistant", "content": assistant_message["content"]})

            tool_calls = assistant_message.get("tool_calls", [])
            if not tool_calls:
                return assistant_message["content"]

            for tool_call in tool_calls:
                self._execute_tool_call(tool_call, context)

        logger.warning("Agent loop exceeded max steps without final assistant response")
        return "I was unable to finish the request in the allotted number of steps."

    def _normalize_response(self, response: Any) -> Dict[str, Any]:
        """Normalize model output into a dict with optional tool calls."""
        if isinstance(response, str):
            return {"content": response}
        if isinstance(response, dict):
            content = response.get("content") or response.get("text") or ""
            tool_calls = response.get("tool_calls") or []
            if isinstance(tool_calls, str):
                try:
                    tool_calls = json.loads(tool_calls)
                except json.JSONDecodeError:
                    tool_calls = []
            if not isinstance(tool_calls, list):
                tool_calls = []

            if not tool_calls and isinstance(content, str):
                try:
                    parsed = json.loads(content)
                    if isinstance(parsed, dict):
                        if isinstance(parsed.get("tool_calls"), list):
                            tool_calls = parsed["tool_calls"]
                        if parsed.get("content") is not None:
                            content = parsed["content"]
                except json.JSONDecodeError:
                    pass

            return {"content": str(content), "tool_calls": tool_calls}
        return {"content": str(response), "tool_calls": []}

    def _execute_tool_call(self, tool_call: Dict[str, Any], context: Any) -> None:
        """Execute one tool call and append the result to the conversation history."""
        name = tool_call.get("name") or ""
        arguments = tool_call.get("arguments") or {}
        if not isinstance(arguments, dict):
            arguments = {}

        if not name:
            tool_result = {"error": "Missing tool name"}
        else:
            tool = self.registry.get(name)
            if tool is None:
                tool_result = {"error": f"Unknown tool: {name}"}
            else:
                try:
                    result = self.registry.invoke(name, arguments, context=context)
                    tool_result = {"result": result}
                except Exception as exc:  # pragma: no cover - runtime path
                    tool_result = {"error": str(exc)}

        logger.info("Tool call %s -> %s", name, json.dumps(tool_result, ensure_ascii=False))
        self.history.append({
            "role": "tool",
            "name": name,
            "content": json.dumps(tool_result, ensure_ascii=False),
        })
