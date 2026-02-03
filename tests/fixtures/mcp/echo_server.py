#!/usr/bin/env python3
"""Simple Echo MCP server for integration testing.

This server implements the MCP protocol over stdio and provides
simple tools for testing MCP integration.

Tools provided:
- echo: Echoes back the input message
- add: Adds two numbers together
- get_time: Returns the current time (for stateless testing)
"""

import json
import sys
from datetime import datetime


def handle_initialize(params: dict) -> dict:
    """Handle initialize request."""
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {},
        },
        "serverInfo": {
            "name": "test-echo-server",
            "version": "1.0.0",
        },
    }


def handle_tools_list(params: dict) -> dict:
    """Handle tools/list request."""
    return {
        "tools": [
            {
                "name": "echo",
                "description": "Echoes back the input message exactly as provided",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "The message to echo back",
                        },
                    },
                    "required": ["message"],
                },
            },
            {
                "name": "add",
                "description": "Adds two numbers together and returns the result",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "a": {
                            "type": "number",
                            "description": "First number",
                        },
                        "b": {
                            "type": "number",
                            "description": "Second number",
                        },
                    },
                    "required": ["a", "b"],
                },
            },
            {
                "name": "get_time",
                "description": "Returns the current UTC time as ISO 8601 string",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
        ],
    }


def handle_tools_call(params: dict) -> dict:
    """Handle tools/call request."""
    tool_name = params.get("name", "")
    arguments = params.get("arguments", {})

    if tool_name == "echo":
        message = arguments.get("message", "")
        return {
            "content": [
                {
                    "type": "text",
                    "text": message,
                }
            ],
        }

    elif tool_name == "add":
        a = arguments.get("a", 0)
        b = arguments.get("b", 0)
        result = a + b
        return {
            "content": [
                {
                    "type": "text",
                    "text": str(result),
                }
            ],
        }

    elif tool_name == "get_time":
        current_time = datetime.utcnow().isoformat() + "Z"
        return {
            "content": [
                {
                    "type": "text",
                    "text": current_time,
                }
            ],
        }

    else:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Unknown tool: {tool_name}",
                }
            ],
            "isError": True,
        }


def handle_request(request: dict) -> dict:
    """Route request to appropriate handler."""
    method = request.get("method", "")
    params = request.get("params", {})

    handlers = {
        "initialize": handle_initialize,
        "tools/list": handle_tools_list,
        "tools/call": handle_tools_call,
    }

    handler = handlers.get(method)
    if handler:
        return handler(params)
    else:
        raise ValueError(f"Unknown method: {method}")


def send_response(response_id, result: dict = None, error: dict = None):
    """Send JSON-RPC response to stdout."""
    response = {
        "jsonrpc": "2.0",
        "id": response_id,
    }

    if error:
        response["error"] = error
    else:
        response["result"] = result

    sys.stdout.write(json.dumps(response) + "\n")
    sys.stdout.flush()


def main():
    """Main MCP server loop."""
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                # EOF, exit gracefully
                break

            line = line.strip()
            if not line:
                continue

            request = json.loads(line)
            request_id = request.get("id")

            try:
                result = handle_request(request)
                send_response(request_id, result=result)
            except ValueError as e:
                send_response(
                    request_id,
                    error={
                        "code": -32601,
                        "message": str(e),
                    },
                )

        except json.JSONDecodeError as e:
            # Invalid JSON
            send_response(
                None,
                error={
                    "code": -32700,
                    "message": f"Parse error: {e}",
                },
            )
        except Exception as e:
            # Internal error
            send_response(
                None,
                error={
                    "code": -32603,
                    "message": f"Internal error: {e}",
                },
            )


if __name__ == "__main__":
    main()
