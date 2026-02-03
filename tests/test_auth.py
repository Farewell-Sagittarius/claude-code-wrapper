"""Tests for authentication and authorization."""

import pytest
from fastapi.testclient import TestClient


class TestAuthentication:
    """Test API key authentication."""

    def test_missing_api_key(self, client: TestClient):
        """Request without API key should fail with 401."""
        response = client.post(
            "/v1/messages",
            json={
                "model": "claude-code-opus",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": "test"}],
            },
        )
        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["error"]["type"] == "invalid_request_error"
        assert "API key" in data["detail"]["error"]["message"]

    def test_invalid_api_key(self, client: TestClient):
        """Request with invalid API key should fail with 401."""
        response = client.post(
            "/v1/messages",
            headers={
                "Authorization": "Bearer invalid-key-12345",
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": "claude-code-opus",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": "test"}],
            },
        )
        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["error"]["code"] == "invalid_api_key"

    def test_malformed_auth_header(self, client: TestClient):
        """Request with malformed Authorization header should fail."""
        response = client.post(
            "/v1/messages",
            headers={
                "Authorization": "NotBearer sk-light-dev",
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": "claude-code-opus",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": "test"}],
            },
        )
        assert response.status_code == 401


class TestAuthorizationModes:
    """Test different authorization/tool modes."""

    def test_sessions_no_auth_required(self, client: TestClient):
        """Sessions endpoint does not require authentication."""
        response = client.get("/v1/sessions")
        assert response.status_code == 200

    def test_messages_requires_auth(self, client: TestClient):
        """Messages endpoint should require authentication."""
        response = client.post(
            "/v1/messages",
            json={
                "model": "claude-code-opus",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": "test"}],
            },
        )
        assert response.status_code == 401
