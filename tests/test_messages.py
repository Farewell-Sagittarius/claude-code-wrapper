"""Tests for Anthropic Messages API endpoint.

Combines validation tests (fast) and essential integration tests.
"""

import pytest
from fastapi.testclient import TestClient


class TestRequestValidation:
    """Test request validation (fast, no API calls)."""

    def test_missing_model(self, client: TestClient, anthropic_headers: dict):
        """Request without model should fail validation."""
        response = client.post(
            "/v1/messages",
            headers=anthropic_headers,
            json={
                "max_tokens": 100,
                "messages": [{"role": "user", "content": "test"}],
            },
        )
        assert response.status_code == 422

    def test_missing_messages(self, client: TestClient, anthropic_headers: dict):
        """Request without messages should fail validation."""
        response = client.post(
            "/v1/messages",
            headers=anthropic_headers,
            json={"model": "claude-code-opus", "max_tokens": 100},
        )
        assert response.status_code == 422

    def test_invalid_json(self, client: TestClient, basic_headers: dict):
        """Invalid JSON should return 422."""
        response = client.post(
            "/v1/messages",
            headers=basic_headers,
            content="not valid json",
        )
        assert response.status_code == 422


class TestBasicMessaging:
    """Test basic messaging functionality."""

    @pytest.mark.integration
    def test_simple_message(self, client: TestClient, anthropic_headers: dict):
        """Simple message should return valid response."""
        response = client.post(
            "/v1/messages",
            headers=anthropic_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 50,
                "messages": [{"role": "user", "content": "Say 'ok'"}],
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["type"] == "message"
        assert data["id"].startswith("msg_")
        assert data["role"] == "assistant"
        assert "content" in data
        assert "usage" in data
        assert "input_tokens" in data["usage"]
        assert "output_tokens" in data["usage"]

    @pytest.mark.integration
    def test_streaming(self, client: TestClient, anthropic_headers: dict):
        """Streaming should return SSE events."""
        with client.stream(
            "POST",
            "/v1/messages",
            headers=anthropic_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 50,
                "messages": [{"role": "user", "content": "Say 'ok'"}],
                "stream": True,
            },
        ) as response:
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")


class TestExtensionParameters:
    """Test wrapper extension parameters."""

    @pytest.mark.integration
    def test_session_id(self, client: TestClient, anthropic_headers: dict):
        """session_id extension should be accepted."""
        response = client.post(
            "/v1/messages",
            headers=anthropic_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 50,
                "messages": [{"role": "user", "content": "Say 'ok'"}],
                "session_id": "test-session",
            },
        )
        assert response.status_code == 200
