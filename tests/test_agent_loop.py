import json
import unittest

from agent import QuotationAgent
from tool_registry import ToolRegistry


class FakeLLM:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def generate(self, messages, tools):
        self.calls.append((messages, tools))
        if not self.responses:
            return {"content": "Done."}
        return self.responses.pop(0)


class QuotationAgentTests(unittest.TestCase):
    def setUp(self):
        self.registry = ToolRegistry()
        from agent import QuotationAgent
        QuotationAgent(llm_client=None, registry=self.registry).registry.list_tools()

    def test_registry_contains_required_tools(self):
        tool_names = {tool.name for tool in self.registry.list_tools()}
        required = {
            "search_products",
            "add_to_cart",
            "remove_from_cart",
            "update_quantity",
            "show_cart",
            "generate_quotation",
            "generate_pdf",
            "clear_cart",
        }
        self.assertTrue(required.issubset(tool_names))

    def test_agent_executes_tool_and_returns_final_response(self):
        class Context:
            def __init__(self):
                self.session = {"cart": []}
                self.db = None
                self.pdf_generator = None

        context = Context()
        fake_llm = FakeLLM([
            {"content": json.dumps({"tool_calls": [{"name": "show_cart", "arguments": {}}]})},
            {"content": "The cart is empty."},
        ])

        agent = QuotationAgent(llm_client=fake_llm, registry=self.registry,
                               context_factory=lambda: context)
        response = agent.run("show my cart")

        self.assertEqual(response, "The cart is empty.")
        self.assertEqual(fake_llm.calls[0][0][0]["content"], "show my cart")
        self.assertEqual(len(fake_llm.calls), 2)

    def test_agent_handles_invalid_tool_name(self):
        class Context:
            def __init__(self):
                self.session = {"cart": []}
                self.db = None
                self.pdf_generator = None

        context = Context()
        fake_llm = FakeLLM([
            {"content": json.dumps({"tool_calls": [{"name": "not_a_real_tool", "arguments": {}}]})},
            {"content": "I couldn't find that tool."},
        ])

        agent = QuotationAgent(llm_client=fake_llm, registry=self.registry,
                               context_factory=lambda: context)
        response = agent.run("use a missing tool")

        self.assertEqual(response, "I couldn't find that tool.")


if __name__ == "__main__":
    unittest.main()
