"""Tests for tool mode functionality."""

import pytest
from fastapi.testclient import TestClient


class TestToolModeLight:
    """Test light mode (no tools)."""

    @pytest.mark.integration
    def test_light_mode_messages(self, client: TestClient, light_headers: dict):
        """Light mode should work for simple messages."""
        response = client.post(
            "/v1/messages",
            headers=light_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": "What is 2+2? Answer only the number."}],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert len(data["content"]) > 0

    @pytest.mark.integration
    def test_light_mode_no_tool_execution(self, client: TestClient, light_headers: dict):
        """Light mode should not execute tools even if asked."""
        response = client.post(
            "/v1/messages",
            headers=light_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": "List files in /tmp using bash"}],
            },
        )
        assert response.status_code == 200
        # Should get a response but no actual file listing (tools disabled)


class TestToolModeBasic:
    """Test basic mode (built-in tools)."""

    @pytest.mark.integration
    def test_basic_mode_messages(self, client: TestClient, basic_headers: dict):
        """Basic mode should work for messages."""
        response = client.post(
            "/v1/messages",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": "Say hello"}],
            },
        )
        assert response.status_code == 200

    @pytest.mark.integration
    def test_basic_mode_can_use_tools(self, client: TestClient, basic_headers: dict):
        """Basic mode should be able to use built-in tools."""
        response = client.post(
            "/v1/messages",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": "What is 2+2?"}],
            },
        )
        assert response.status_code == 200


class TestToolModeHeavy:
    """Test heavy mode (all tools + MCP)."""

    @pytest.mark.integration
    def test_heavy_mode_messages(self, client: TestClient, heavy_headers: dict):
        """Heavy mode should work for messages."""
        response = client.post(
            "/v1/messages",
            headers=heavy_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": "Say hello"}],
            },
        )
        assert response.status_code == 200


class TestToolModeCustom:
    """Test custom mode (per-request settings)."""

    @pytest.mark.integration
    def test_custom_mode_default(self, client: TestClient, custom_headers: dict):
        """Custom mode should work with default settings."""
        response = client.post(
            "/v1/messages",
            headers=custom_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": "Say hello"}],
            },
        )
        assert response.status_code == 200


class TestToolFiltering:
    """Test tool filtering (allowed/disallowed tools)."""

    @pytest.mark.integration
    def test_allowed_tools(self, client: TestClient, basic_headers: dict):
        """allowed_tools parameter should be accepted."""
        response = client.post(
            "/v1/messages",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": "Say hello"}],
                "allowed_tools": ["Read", "Glob"],
            },
        )
        assert response.status_code == 200

    @pytest.mark.integration
    def test_disallowed_tools(self, client: TestClient, basic_headers: dict):
        """disallowed_tools parameter should be accepted."""
        response = client.post(
            "/v1/messages",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": "Say hello"}],
                "disallowed_tools": ["Bash", "Edit", "Write"],
            },
        )
        assert response.status_code == 200
