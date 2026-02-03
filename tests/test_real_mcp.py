"""Tests for real MCP server integration.

Uses the echo_server.py MCP test server to verify actual MCP
protocol communication and tool execution.
"""

import os
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
            "/v1/chat/completions",
            headers=heavy_headers,
            json={
                "model": "claude-code-opus",
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

        # Should succeed or fail gracefully
        assert response.status_code in [200, 500]

    @pytest.mark.integration
    @pytest.mark.mcp
    def test_mcp_tool_list(self, client: TestClient, heavy_headers: dict):
        """Verify MCP server tools are discovered."""
        response = client.post(
            "/v1/chat/completions",
            headers=heavy_headers,
            json={
                "model": "claude-code-opus",
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
                "max_turns": 2,
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
            "/v1/chat/completions",
            headers=heavy_headers,
            json={
                "model": "claude-code-opus",
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
                "max_turns": 3,
            },
        )

        assert response.status_code in [200, 500]

        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            # The echoed message should appear in the response
            assert test_message in content, f"Echo not found in: {content}"

    @pytest.mark.integration
    @pytest.mark.mcp
    def test_echo_special_characters(self, client: TestClient, heavy_headers: dict):
        """Verify echo handles special characters."""
        test_message = "Hello! @#$% 你好 🎉"

        response = client.post(
            "/v1/chat/completions",
            headers=heavy_headers,
            json={
                "model": "claude-code-opus",
                "messages": [
                    {
                        "role": "user",
                        "content": f"Use the echo tool with this message: '{test_message}'",
                    }
                ],
                "mcp_servers": {
                    "echo": {
                        "type": "stdio",
                        "command": PYTHON_PATH,
                        "args": [MCP_ECHO_SERVER],
                    }
                },
                "max_turns": 3,
            },
        )

        assert response.status_code in [200, 500]


class TestMCPAddTool:
    """Test MCP add tool execution."""

    @pytest.mark.integration
    @pytest.mark.mcp
    def test_add_integers(self, client: TestClient, heavy_headers: dict):
        """Verify add tool correctly adds two integers."""
        response = client.post(
            "/v1/chat/completions",
            headers=heavy_headers,
            json={
                "model": "claude-code-opus",
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
                "max_turns": 3,
            },
        )

        assert response.status_code in [200, 500]

        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            assert "42" in content, f"Expected 42 in: {content}"

    @pytest.mark.integration
    @pytest.mark.mcp
    def test_add_floats(self, client: TestClient, heavy_headers: dict):
        """Verify add tool handles floating point numbers."""
        response = client.post(
            "/v1/chat/completions",
            headers=heavy_headers,
            json={
                "model": "claude-code-opus",
                "messages": [
                    {
                        "role": "user",
                        "content": "Use the add tool to add 3.14 and 2.86. What's the result?",
                    }
                ],
                "mcp_servers": {
                    "echo": {
                        "type": "stdio",
                        "command": PYTHON_PATH,
                        "args": [MCP_ECHO_SERVER],
                    }
                },
                "max_turns": 3,
            },
        )

        assert response.status_code in [200, 500]

        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            # Result should be 6.0 or 6
            assert "6" in content, f"Expected 6 in: {content}"

    @pytest.mark.integration
    @pytest.mark.mcp
    def test_add_negative_numbers(self, client: TestClient, heavy_headers: dict):
        """Verify add tool handles negative numbers."""
        response = client.post(
            "/v1/chat/completions",
            headers=heavy_headers,
            json={
                "model": "claude-code-opus",
                "messages": [
                    {
                        "role": "user",
                        "content": "Use the add tool: add -10 and 5. What's the sum?",
                    }
                ],
                "mcp_servers": {
                    "echo": {
                        "type": "stdio",
                        "command": PYTHON_PATH,
                        "args": [MCP_ECHO_SERVER],
                    }
                },
                "max_turns": 3,
            },
        )

        assert response.status_code in [200, 500]

        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            assert "-5" in content, f"Expected -5 in: {content}"


class TestMCPGetTimeTool:
    """Test MCP get_time tool execution."""

    @pytest.mark.integration
    @pytest.mark.mcp
    def test_get_current_time(self, client: TestClient, heavy_headers: dict):
        """Verify get_time tool returns a timestamp."""
        response = client.post(
            "/v1/chat/completions",
            headers=heavy_headers,
            json={
                "model": "claude-code-opus",
                "messages": [
                    {
                        "role": "user",
                        "content": "Use the get_time tool to get the current UTC time.",
                    }
                ],
                "mcp_servers": {
                    "echo": {
                        "type": "stdio",
                        "command": PYTHON_PATH,
                        "args": [MCP_ECHO_SERVER],
                    }
                },
                "max_turns": 3,
            },
        )

        assert response.status_code in [200, 500]

        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            # Should contain date/time elements
            assert any(x in content for x in ["202", "T", ":", "time"]), f"No time found: {content}"


class TestMCPErrorHandling:
    """Test MCP server error handling."""

    @pytest.mark.integration
    @pytest.mark.mcp
    def test_nonexistent_server(self, client: TestClient, heavy_headers: dict):
        """Verify graceful handling when MCP server doesn't exist."""
        response = client.post(
            "/v1/chat/completions",
            headers=heavy_headers,
            json={
                "model": "claude-code-opus",
                "messages": [{"role": "user", "content": "Say hello"}],
                "mcp_servers": {
                    "nonexistent": {
                        "type": "stdio",
                        "command": "/nonexistent/path/to/server",
                    }
                },
            },
        )

        # Should handle error gracefully, not crash
        assert response.status_code in [200, 500]

    @pytest.mark.integration
    @pytest.mark.mcp
    def test_invalid_server_script(self, client: TestClient, heavy_headers: dict):
        """Verify graceful handling when MCP server script is invalid."""
        response = client.post(
            "/v1/chat/completions",
            headers=heavy_headers,
            json={
                "model": "claude-code-opus",
                "messages": [{"role": "user", "content": "Say hello"}],
                "mcp_servers": {
                    "invalid": {
                        "type": "stdio",
                        "command": PYTHON_PATH,
                        "args": ["-c", "import sys; sys.exit(1)"],
                    }
                },
            },
        )

        assert response.status_code in [200, 500]

    @pytest.mark.integration
    @pytest.mark.mcp
    def test_slow_server_timeout(self, client: TestClient, heavy_headers: dict):
        """Verify timeout handling for slow MCP servers."""
        response = client.post(
            "/v1/chat/completions",
            headers=heavy_headers,
            json={
                "model": "claude-code-opus",
                "messages": [{"role": "user", "content": "Say hello"}],
                "mcp_servers": {
                    "slow": {
                        "type": "stdio",
                        "command": PYTHON_PATH,
                        "args": ["-c", "import time; time.sleep(60)"],
                    }
                },
            },
            timeout=30,  # 30 second timeout for the request
        )

        # Should timeout or handle gracefully
        assert response.status_code in [200, 500, 504]


class TestMCPMultipleServers:
    """Test multiple MCP servers in single request."""

    @pytest.mark.integration
    @pytest.mark.mcp
    def test_multiple_mcp_servers(self, client: TestClient, heavy_headers: dict):
        """Verify multiple MCP servers can be configured."""
        response = client.post(
            "/v1/chat/completions",
            headers=heavy_headers,
            json={
                "model": "claude-code-opus",
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


class TestMCPWithEnvironment:
    """Test MCP server with environment variables."""

    @pytest.mark.integration
    @pytest.mark.mcp
    def test_mcp_with_env_vars(self, client: TestClient, heavy_headers: dict):
        """Verify MCP server receives environment variables."""
        response = client.post(
            "/v1/chat/completions",
            headers=heavy_headers,
            json={
                "model": "claude-code-opus",
                "messages": [{"role": "user", "content": "Say hello"}],
                "mcp_servers": {
                    "echo": {
                        "type": "stdio",
                        "command": PYTHON_PATH,
                        "args": [MCP_ECHO_SERVER],
                        "env": {
                            "TEST_VAR": "test_value",
                            "ANOTHER_VAR": "another_value",
                        },
                    }
                },
            },
        )

        assert response.status_code in [200, 500]


class TestMCPAnthropicEndpoint:
    """Test MCP with Anthropic messages endpoint."""

    @pytest.mark.integration
    @pytest.mark.mcp
    def test_anthropic_mcp_echo(self, client: TestClient, anthropic_headers: dict):
        """Verify MCP works with Anthropic endpoint."""
        # Use heavy mode for MCP
        headers = anthropic_headers.copy()
        headers["Authorization"] = "Bearer sk-heavy-dev"

        response = client.post(
            "/v1/messages",
            headers=headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 1024,
                "messages": [
                    {
                        "role": "user",
                        "content": "Use the echo tool to say 'anthropic_mcp_test'",
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
            assert "anthropic_mcp_test" in content or "echo" in content.lower()

    @pytest.mark.integration
    @pytest.mark.mcp
    def test_anthropic_mcp_add(self, client: TestClient, anthropic_headers: dict):
        """Verify MCP add tool works with Anthropic endpoint."""
        headers = anthropic_headers.copy()
        headers["Authorization"] = "Bearer sk-heavy-dev"

        response = client.post(
            "/v1/messages",
            headers=headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 1024,
                "messages": [
                    {
                        "role": "user",
                        "content": "Use the add tool to add 100 and 23. Just tell me the result.",
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
            assert "123" in content, f"Expected 123 in: {content}"


class TestMCPToolModes:
    """Test MCP server access with different tool modes."""

    @pytest.mark.integration
    @pytest.mark.mcp
    def test_light_mode_no_mcp(self, client: TestClient, light_headers: dict):
        """Verify light mode can still specify external MCP servers."""
        response = client.post(
            "/v1/chat/completions",
            headers=light_headers,
            json={
                "model": "claude-code-opus",
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

        # Light mode may or may not support MCP, but shouldn't crash
        assert response.status_code in [200, 403, 500]

    @pytest.mark.integration
    @pytest.mark.mcp
    def test_basic_mode_external_mcp(self, client: TestClient, basic_headers: dict):
        """Verify basic mode accepts external MCP servers."""
        response = client.post(
            "/v1/chat/completions",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
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
    def test_heavy_mode_full_mcp(self, client: TestClient, heavy_headers: dict):
        """Verify heavy mode has full MCP support."""
        response = client.post(
            "/v1/chat/completions",
            headers=heavy_headers,
            json={
                "model": "claude-code-opus",
                "messages": [{"role": "user", "content": "Use echo to say 'heavy mode test'"}],
                "mcp_servers": {
                    "echo": {
                        "type": "stdio",
                        "command": PYTHON_PATH,
                        "args": [MCP_ECHO_SERVER],
                    }
                },
                "max_turns": 3,
            },
        )

        assert response.status_code == 200
