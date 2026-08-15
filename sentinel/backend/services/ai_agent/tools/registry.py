"""Tool Registry — the only execution boundary between the agent and tools.

The AI Agent calls registry.invoke(tool_name, arguments).
It never imports individual tool modules directly.

The registry exposes to the agent:
  - tool name
  - description
  - input schema (JSON Schema)

The callable implementation remains internal to the registry.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from services.ai_agent.models import ToolCall, ToolResult


class ToolNotFoundError(Exception):
    """Raised when the agent requests a tool that is not registered."""


@dataclass
class _RegistryEntry:
    name:         str
    description:  str
    input_schema: dict[str, Any]
    function:     Callable[[dict[str, Any]], ToolResult]


class ToolRegistry:
    """Register tools and dispatch tool calls on behalf of the agent.

    The agent sees only name + description + input_schema.
    The implementation callable is never exposed outside this class.
    """

    def __init__(self) -> None:
        self._tools: dict[str, _RegistryEntry] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self,
        name:         str,
        description:  str,
        input_schema: dict[str, Any],
        function:     Callable[[dict[str, Any]], ToolResult],
    ) -> None:
        if name in self._tools:
            raise ValueError(f"Tool '{name}' is already registered.")
        self._tools[name] = _RegistryEntry(
            name         = name,
            description  = description,
            input_schema = input_schema,
            function     = function,
        )

    # ------------------------------------------------------------------
    # Agent-facing interface
    # ------------------------------------------------------------------

    def get_tool_descriptions(self) -> list[dict[str, Any]]:
        """Return name, description, and input_schema for every registered tool.

        Callables are deliberately excluded — the agent must not access them.
        """
        return [
            {
                "name":         e.name,
                "description":  e.description,
                "input_schema": e.input_schema,
            }
            for e in self._tools.values()
        ]

    def invoke(self, tool_name: str, arguments: dict[str, Any]) -> ToolResult:
        """Execute a tool call and return a structured ToolResult observation.

        Raises ToolNotFoundError for unknown tools — never a raw KeyError.
        Normal investigative failures (not_found, invalid_input) are returned
        as ToolResult values, not exceptions.
        """
        if tool_name not in self._tools:
            raise ToolNotFoundError(
                f"Tool '{tool_name}' is not registered. "
                f"Available tools: {sorted(self._tools)}"
            )
        entry = self._tools[tool_name]
        return entry.function(arguments)

    def invoke_call(self, tool_call: ToolCall) -> ToolResult:
        """Convenience wrapper that accepts a ToolCall model."""
        return self.invoke(tool_call.tool_name, tool_call.arguments)

    def __contains__(self, tool_name: str) -> bool:
        return tool_name in self._tools

    def __len__(self) -> int:
        return len(self._tools)
