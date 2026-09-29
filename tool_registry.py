"""Registry and execution helpers for agent tools."""

import inspect
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ToolSpec:
    """Metadata describing a callable tool."""

    name: str
    description: str
    func: Callable[..., Any]
    parameters: Optional[Dict[str, Any]] = None


class ToolRegistry:
    """Register tools and expose a schema that the LLM can reason about."""

    def __init__(self):
        self._tools: Dict[str, ToolSpec] = {}

    def register(self, tool: ToolSpec) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[ToolSpec]:
        return self._tools.get(name)

    def list_tools(self) -> List[ToolSpec]:
        return list(self._tools.values())

    def to_openai_schema(self) -> List[Dict[str, Any]]:
        """Return a simple OpenAI-style tool schema list."""
        tools = []
        for tool in self.list_tools():
            schema = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters or {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            }
            tools.append(schema)
        return tools

    def invoke(self, name: str, arguments: Optional[Dict[str, Any]] = None, context: Optional[Any] = None) -> Any:
        """Invoke a tool by name, handling invalid names and argument issues."""
        tool = self.get(name)
        if tool is None:
            raise KeyError(f"Unknown tool: {name}")

        args = arguments or {}
        if not isinstance(args, dict):
            raise TypeError("Tool arguments must be a dictionary")

        try:
            logger.info("Executing tool %s with arguments %s", name, json.dumps(args, ensure_ascii=False))
            return tool.func(context=context, **args)
        except TypeError as exc:
            logger.exception("Tool %s failed with invalid arguments: %s", name, exc)
            raise ValueError(f"Invalid arguments for tool {name}: {exc}") from exc
