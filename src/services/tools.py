"""Tool classification and management for external tool support."""

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# Internal tools provided by Claude Agent SDK
# These are handled by the SDK automatically and should not be passed to clients
INTERNAL_TOOLS: Set[str] = {
    # File operations
    "Read",
    "Write",
    "Edit",
    "MultiEdit",
    # Shell operations
    "Bash",
    # Search operations
    "Glob",
    "Grep",
    "LS",
    # Web operations
    "WebFetch",
    "WebSearch",
    # Task management
    "TodoRead",
    "TodoWrite",
    "Task",
    # Jupyter
    "Jupyter",
    "NotebookEdit",
}


def classify_tools(
    tools: List[Dict[str, Any]],
) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Classify tools into internal (SDK-handled) and external (client-handled).

    Args:
        tools: List of tool definitions in Anthropic format
            Each tool should have 'name', 'description', and 'input_schema'

    Returns:
        Tuple of (internal_tool_names, external_tool_definitions)
        - internal_tool_names: List of tool names to enable in SDK
        - external_tool_definitions: List of full tool defs for external tools
    """
    internal: List[str] = []
    external: List[Dict[str, Any]] = []

    for tool in tools:
        name = tool.get("name", "")
        if name in INTERNAL_TOOLS:
            internal.append(name)
            logger.debug(f"Tool '{name}' classified as internal")
        else:
            external.append(tool)
            logger.debug(f"Tool '{name}' classified as external")

    logger.info(
        f"Classified {len(tools)} tools: "
        f"{len(internal)} internal, {len(external)} external"
    )

    return internal, external


def is_internal_tool(name: str) -> bool:
    """Check if a tool name is an internal SDK tool."""
    return name in INTERNAL_TOOLS


@dataclass
class PendingToolUse:
    """Information about a tool call that needs client execution."""

    id: str
    name: str
    input: Dict[str, Any]


@dataclass
class ExternalToolsContext:
    """Context for tracking external tool calls during a request."""

    external_tool_names: Set[str] = field(default_factory=set)
    pending_tool_use: Optional[PendingToolUse] = None

    def is_external(self, name: str) -> bool:
        """Check if a tool name is an external tool for this request."""
        return name in self.external_tool_names


def create_external_tools_mcp_config(
    tools: List[Dict[str, Any]],
) -> Tuple[Dict[str, Any], Set[str]]:
    """
    Create MCP server configuration for external tools.

    This creates a configuration that registers external tools with the SDK,
    allowing Claude to know about and attempt to call them.

    Args:
        tools: List of external tool definitions

    Returns:
        Tuple of (mcp_config dict, set of external tool names)
    """
    try:
        from claude_agent_sdk import SdkMcpTool, create_sdk_mcp_server
    except ImportError:
        logger.error("claude-agent-sdk not available for external tools")
        return {}, set()

    sdk_tools = []
    tool_names = set()

    for tool_def in tools:
        name = tool_def.get("name", "")
        description = tool_def.get("description", "")
        input_schema = tool_def.get("input_schema", {"type": "object", "properties": {}})

        # Create SDK tool (handler won't actually be called - we intercept via can_use_tool)
        async def dummy_handler(**kwargs):
            # This should never be reached due to can_use_tool interception
            raise RuntimeError(f"External tool handler called unexpectedly")

        sdk_tools.append(
            SdkMcpTool(
                name=name,
                description=description,
                inputSchema=input_schema,
                handler=dummy_handler,
            )
        )
        tool_names.add(name)

    if not sdk_tools:
        return {}, set()

    # Create MCP server config
    mcp_config = create_sdk_mcp_server("external_tools", tools=sdk_tools)
    logger.info(f"Created external tools MCP config with {len(sdk_tools)} tools: {tool_names}")

    return {"external_tools": mcp_config}, tool_names


def create_can_use_tool_callback(
    context: ExternalToolsContext,
) -> Callable:
    """
    Create a can_use_tool callback that intercepts external tool calls.

    When Claude tries to use an external tool, this callback denies the
    request with interrupt=True, causing the SDK to stop and return the
    tool_use information to us.

    Args:
        context: ExternalToolsContext to store pending tool information

    Returns:
        Async callback function for can_use_tool
    """
    try:
        from claude_agent_sdk import (
            PermissionResultAllow,
            PermissionResultDeny,
            ToolPermissionContext,
        )
    except ImportError:
        logger.error("claude-agent-sdk not available")
        return None

    async def can_use_tool_callback(
        tool_name: str,
        tool_input: Dict[str, Any],
        permission_context: ToolPermissionContext,
    ):
        """Intercept tool calls and deny external tools."""
        if context.is_external(tool_name):
            # Store tool use information for returning to client
            context.pending_tool_use = PendingToolUse(
                id=getattr(permission_context, "tool_use_id", f"toolu_{tool_name}"),
                name=tool_name,
                input=tool_input,
            )
            logger.debug(f"Intercepted external tool: {tool_name}")
            # Deny and interrupt - this will cause SDK to return control to us
            return PermissionResultDeny(
                message=f"External tool '{tool_name}' - returning to client",
                interrupt=True,
            )

        # Allow internal tools
        logger.debug(f"Allowing internal tool: {tool_name}")
        return PermissionResultAllow()

    return can_use_tool_callback
