"""AI Agent tools package.

Exports build_registry() which returns a ToolRegistry pre-loaded with
all four Operation Nightfall investigative tools.

agent.py interacts only with ToolRegistry — it never imports the
individual tool modules directly.
"""
from .registry import ToolRegistry, ToolNotFoundError
from .vehicle_records import (
    lookup_vehicle,
    VEHICLE_TOOL_NAME,
    VEHICLE_TOOL_DESCRIPTION,
    VEHICLE_TOOL_SCHEMA,
)
from .access_logs import (
    query_access_logs,
    ACCESS_TOOL_NAME,
    ACCESS_TOOL_DESCRIPTION,
    ACCESS_TOOL_SCHEMA,
)
from .surveillance import (
    query_surveillance,
    SURVEILLANCE_TOOL_NAME,
    SURVEILLANCE_TOOL_DESCRIPTION,
    SURVEILLANCE_TOOL_SCHEMA,
)
from .financial_intelligence import (
    query_financial_intelligence,
    FINANCIAL_TOOL_NAME,
    FINANCIAL_TOOL_DESCRIPTION,
    FINANCIAL_TOOL_SCHEMA,
)


def build_registry() -> ToolRegistry:
    """Return a ToolRegistry loaded with all four investigative tools."""
    registry = ToolRegistry()
    registry.register(
        name         = VEHICLE_TOOL_NAME,
        description  = VEHICLE_TOOL_DESCRIPTION,
        input_schema = VEHICLE_TOOL_SCHEMA,
        function     = lookup_vehicle,
    )
    registry.register(
        name         = ACCESS_TOOL_NAME,
        description  = ACCESS_TOOL_DESCRIPTION,
        input_schema = ACCESS_TOOL_SCHEMA,
        function     = query_access_logs,
    )
    registry.register(
        name         = SURVEILLANCE_TOOL_NAME,
        description  = SURVEILLANCE_TOOL_DESCRIPTION,
        input_schema = SURVEILLANCE_TOOL_SCHEMA,
        function     = query_surveillance,
    )
    registry.register(
        name         = FINANCIAL_TOOL_NAME,
        description  = FINANCIAL_TOOL_DESCRIPTION,
        input_schema = FINANCIAL_TOOL_SCHEMA,
        function     = query_financial_intelligence,
    )
    return registry


__all__ = [
    "ToolRegistry",
    "ToolNotFoundError",
    "build_registry",
]
