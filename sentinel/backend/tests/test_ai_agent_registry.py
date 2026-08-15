"""Tests for ToolRegistry.

Covers:
  - Tool registration and retrieval
  - invoke() dispatches to correct function
  - invoke_call() uses ToolCall model
  - ToolNotFoundError on unknown tool name
  - get_tool_descriptions() exposes schema, not callables
  - Duplicate registration raises ValueError
"""
import pytest

from services.ai_agent.tools.registry import ToolRegistry, ToolNotFoundError
from services.ai_agent.models import ToolCall, ToolResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_echo_tool(name: str):
    """Returns a simple function that echoes its arguments as result."""
    def _fn(arguments: dict) -> ToolResult:
        return ToolResult(
            call_id       = arguments.get("_call_id", ""),
            tool_name     = name,
            status        = "success",
            result        = {"echo": arguments},
            query_summary = f"{name}: echo",
        )
    return _fn


_ECHO_SCHEMA = {
    "type": "object",
    "properties": {"value": {"type": "string"}},
    "required": ["value"],
}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class TestRegistration:
    def test_register_and_invoke(self):
        reg = ToolRegistry()
        reg.register("echo", "Echo tool", _ECHO_SCHEMA, _make_echo_tool("echo"))
        result = reg.invoke("echo", {"value": "hello"})
        assert result.status == "success"
        assert result.result["echo"]["value"] == "hello"

    def test_unknown_tool_raises(self):
        reg = ToolRegistry()
        with pytest.raises(ToolNotFoundError):
            reg.invoke("nonexistent_tool", {})

    def test_duplicate_registration_raises(self):
        reg = ToolRegistry()
        reg.register("echo", "Echo tool", _ECHO_SCHEMA, _make_echo_tool("echo"))
        with pytest.raises(ValueError):
            reg.register("echo", "Echo tool again", _ECHO_SCHEMA, _make_echo_tool("echo"))

    def test_get_tool_descriptions_no_callables(self):
        reg = ToolRegistry()
        reg.register("echo", "Echo tool", _ECHO_SCHEMA, _make_echo_tool("echo"))
        descriptions = reg.get_tool_descriptions()
        assert isinstance(descriptions, list)
        for d in descriptions:
            assert "name" in d
            assert "description" in d
            assert "input_schema" in d
            # function callable must NOT be exposed
            assert "function" not in d


# ---------------------------------------------------------------------------
# invoke_call()
# ---------------------------------------------------------------------------

class TestInvokeCall:
    def test_invoke_call_dispatches(self):
        reg = ToolRegistry()
        reg.register("echo", "Echo tool", _ECHO_SCHEMA, _make_echo_tool("echo"))
        tc = ToolCall(tool_name="echo", arguments={"value": "world"})
        result = reg.invoke_call(tc)
        assert result.status == "success"

    def test_invoke_call_unknown_returns_error(self):
        reg = ToolRegistry()
        tc = ToolCall(tool_name="ghost_tool", arguments={})
        with pytest.raises(ToolNotFoundError):
            reg.invoke_call(tc)


# ---------------------------------------------------------------------------
# build_registry — integration smoke test
# ---------------------------------------------------------------------------

class TestBuildRegistry:
    def test_four_tools_registered(self):
        from services.ai_agent.tools import build_registry
        reg = build_registry()
        descriptions = reg.get_tool_descriptions()
        names = {d["name"] for d in descriptions}
        assert "lookup_vehicle"               in names
        assert "query_access_logs"            in names
        assert "query_surveillance"           in names
        assert "query_financial_intelligence" in names

    def test_all_schemas_have_type(self):
        from services.ai_agent.tools import build_registry
        reg = build_registry()
        for d in reg.get_tool_descriptions():
            assert d["input_schema"]["type"] == "object"
