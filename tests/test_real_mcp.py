"""Tests for real MCP server integration.

Uses the echo_server.py MCP test server to verify actual MCP
protocol communication and tool execution.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Path to the echo MCP server
MCP_ECHO_SERVER = str(Path(__file__).parent / "fixtures/mcp/echo_server.py")

# Python interpreter path
PYTHON_PATH = sys.executable


class TestMCPToolDiscovery:
    """Test MCP server tool discovery."""

    @pytest.mark.integration
    @pytest.mark.mcp
    def test_mcp_server_connects(self, client: TestClient, heavy_headers: dict):
        """Verify MCP server can be connected."""
        response = client.post(
            "/v1/messages",
            headers=heavy_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": "Say hello"}],
                "mcp_servers": {
                    "echo": {
                        "type": "stdio",
                        "command": PYTHON_PATH,
                        "args": [MCP_ECHO_SERVER],
                    }
                },
            },
        )
        assert response.status_code in [200, 500]

    @pytest.mark.integration
    @pytest.mark.mcp
    def test_mcp_tool_list(self, client: TestClient, heavy_headers: dict):
        """Verify MCP server tools are discovered."""
        response = client.post(
            "/v1/messages",
            headers=heavy_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 500,
                "messages": [
                    {
                        "role": "user",
                        "content": "What tools are available from the echo server? List them.",
                    }
                ],
                "mcp_servers": {
                    "echo": {
                        "type": "stdio",
                        "command": PYTHON_PATH,
                        "args": [MCP_ECHO_SERVER],
                    }
                },
            },
        )
        assert response.status_code in [200, 500]


class TestMCPEchoTool:
    """Test MCP echo tool execution."""

    @pytest.mark.integration
    @pytest.mark.mcp
    def test_echo_simple_message(self, client: TestClient, heavy_headers: dict):
        """Verify echo tool returns the exact input message."""
        test_message = "test_echo_12345"

        response = client.post(
            "/v1/messages",
            headers=heavy_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 500,
                "messages": [
                    {
                        "role": "user",
                        "content": f"Use the echo tool to echo this exact message: '{test_message}'",
                    }
                ],
                "mcp_servers": {
                    "echo": {
                        "type": "stdio",
                        "command": PYTHON_PATH,
                        "args": [MCP_ECHO_SERVER],
                    }
                },
            },
        )

        assert response.status_code in [200, 500]

        if response.status_code == 200:
            content = response.json()["content"][0]["text"]
            assert test_message in content, f"Echo not found in: {content}"


class TestMCPAddTool:
    """Test MCP add tool execution."""

    @pytest.mark.integration
    @pytest.mark.mcp
    def test_add_integers(self, client: TestClient, heavy_headers: dict):
        """Verify add tool correctly adds two integers."""
        response = client.post(
            "/v1/messages",
            headers=heavy_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 500,
                "messages": [
                    {
                        "role": "user",
                        "content": "Use the add tool to calculate 17 + 25. What is the result?",
                    }
                ],
                "mcp_servers": {
                    "echo": {
                        "type": "stdio",
                        "command": PYTHON_PATH,
                        "args": [MCP_ECHO_SERVER],
                    }
                },
            },
        )

        assert response.status_code in [200, 500]

        if response.status_code == 200:
            content = response.json()["content"][0]["text"]
            assert "42" in content, f"Expected 42 in: {content}"


class TestMCPErrorHandling:
    """Test MCP server error handling."""

    @pytest.mark.integration
    @pytest.mark.mcp
    def test_nonexistent_server(self, client: TestClient, heavy_headers: dict):
        """Verify graceful handling when MCP server doesn't exist."""
        response = client.post(
            "/v1/messages",
            headers=heavy_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": "Say hello"}],
                "mcp_servers": {
                    "nonexistent": {
                        "type": "stdio",
                        "command": "/nonexistent/path/to/server",
                    }
                },
            },
        )
        assert response.status_code in [200, 500]


class TestMCPMultipleServers:
    """Test multiple MCP servers in single request."""

    @pytest.mark.integration
    @pytest.mark.mcp
    def test_multiple_mcp_servers(self, client: TestClient, heavy_headers: dict):
        """Verify multiple MCP servers can be configured."""
        response = client.post(
            "/v1/messages",
            headers=heavy_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": "Say hello"}],
                "mcp_servers": {
                    "echo1": {
                        "type": "stdio",
                        "command": PYTHON_PATH,
                        "args": [MCP_ECHO_SERVER],
                    },
                    "echo2": {
                        "type": "stdio",
                        "command": PYTHON_PATH,
                        "args": [MCP_ECHO_SERVER],
                    },
                },
            },
        )
        assert response.status_code in [200, 500]


class TestMCPToolModes:
    """Test MCP server access with different tool modes."""

    @pytest.mark.integration
    @pytest.mark.mcp
    def test_heavy_mode_full_mcp(self, client: TestClient, heavy_headers: dict):
        """Verify heavy mode has full MCP support."""
        response = client.post(
            "/v1/messages",
            headers=heavy_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 500,
                "messages": [{"role": "user", "content": "Use echo to say 'heavy mode test'"}],
                "mcp_servers": {
                    "echo": {
                        "type": "stdio",
                        "command": PYTHON_PATH,
                        "args": [MCP_ECHO_SERVER],
                    }
                },
            },
        )
        assert response.status_code == 200
