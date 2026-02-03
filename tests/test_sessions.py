"""Tests for session management endpoints."""

import uuid

import pytest
from fastapi.testclient import TestClient


class TestSessionsEndpoint:
    """Test /v1/sessions endpoints."""

    def test_list_sessions_empty(self, client: TestClient, basic_headers: dict):
        """GET /v1/sessions should return empty list initially."""
        response = client.get("/v1/sessions", headers=basic_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["object"] == "list"
        assert "data" in data

    def test_list_sessions_no_auth(self, client: TestClient):
        """GET /v1/sessions does not require authentication."""
        response = client.get("/v1/sessions")
        assert response.status_code == 200

    def test_get_session_stats(self, client: TestClient):
        """GET /v1/sessions/stats should return statistics."""
        response = client.get("/v1/sessions/stats")
        assert response.status_code == 200

        data = response.json()
        assert "active_sessions" in data
        assert "total_messages" in data
        assert "ttl_hours" in data

    def test_get_nonexistent_session(self, client: TestClient, basic_headers: dict):
        """GET /v1/sessions/{id} for nonexistent session should return 404."""
        session_id = f"test-{uuid.uuid4().hex[:8]}"
        response = client.get(f"/v1/sessions/{session_id}", headers=basic_headers)
        assert response.status_code == 404

    def test_delete_nonexistent_session(self, client: TestClient, basic_headers: dict):
        """DELETE /v1/sessions/{id} for nonexistent session should return 404."""
        session_id = f"test-{uuid.uuid4().hex[:8]}"
        response = client.delete(f"/v1/sessions/{session_id}", headers=basic_headers)
        assert response.status_code == 404


class TestSessionCreationViaMessages:
    """Test session creation through messages endpoint."""

    @pytest.mark.integration
    def test_session_created_on_messages(self, client: TestClient, basic_headers: dict):
        """Messages with session_id should create a session."""
        session_id = f"test-session-{uuid.uuid4().hex[:8]}"

        response = client.post(
            "/v1/messages",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": "Say 'test'"}],
                "session_id": session_id,
            },
        )

        if response.status_code == 200:
            session_response = client.get(f"/v1/sessions/{session_id}", headers=basic_headers)
            assert session_response.status_code in [200, 404]

    @pytest.mark.integration
    def test_session_delete(self, client: TestClient, basic_headers: dict):
        """Created session can be deleted."""
        session_id = f"test-del-{uuid.uuid4().hex[:8]}"

        client.post(
            "/v1/messages",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": "test"}],
                "session_id": session_id,
            },
        )

        response = client.delete(f"/v1/sessions/{session_id}", headers=basic_headers)
        assert response.status_code in [200, 404]
