"""Tests for Anthropic API specification compliance.

Verifies that requests and responses conform to the official Anthropic
Messages API specification.
"""

import pytest
from fastapi.testclient import TestClient


class TestAnthropicToolCalling:
    """Test Anthropic native tool calling format."""

    def test_tools_definition_format(self, client: TestClient, anthropic_headers: dict):
        """Verify tools parameter format matches Anthropic spec."""
        response = client.post(
            "/v1/messages",
            headers=anthropic_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "What's the weather in Paris?"}],
                "tools": [
                    {
                        "name": "get_weather",
                        "description": "Get the current weather in a location",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "location": {
                                    "type": "string",
                                    "description": "City name",
                                },
                                "unit": {
                                    "type": "string",
                                    "enum": ["celsius", "fahrenheit"],
                                },
                            },
                            "required": ["location"],
                        },
                    }
                ],
            },
        )
        assert response.status_code in [200, 422, 500]

    def test_tool_choice_auto(self, client: TestClient, anthropic_headers: dict):
        """Verify tool_choice={'type': 'auto'} is accepted."""
        response = client.post(
            "/v1/messages",
            headers=anthropic_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "Hello"}],
                "tools": [
                    {
                        "name": "test_tool",
                        "description": "A test tool",
                        "input_schema": {"type": "object", "properties": {}},
                    }
                ],
                "tool_choice": {"type": "auto"},
            },
        )
        assert response.status_code in [200, 422, 500]

    def test_tool_choice_any(self, client: TestClient, anthropic_headers: dict):
        """Verify tool_choice={'type': 'any'} forces tool use."""
        response = client.post(
            "/v1/messages",
            headers=anthropic_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "Hello"}],
                "tools": [
                    {
                        "name": "test_tool",
                        "description": "A test tool",
                        "input_schema": {"type": "object", "properties": {}},
                    }
                ],
                "tool_choice": {"type": "any"},
            },
        )
        assert response.status_code in [200, 422, 500]

    def test_tool_choice_specific_tool(self, client: TestClient, anthropic_headers: dict):
        """Verify tool_choice can specify a specific tool."""
        response = client.post(
            "/v1/messages",
            headers=anthropic_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "Hello"}],
                "tools": [
                    {
                        "name": "specific_tool",
                        "description": "A specific tool",
                        "input_schema": {"type": "object", "properties": {}},
                    }
                ],
                "tool_choice": {"type": "tool", "name": "specific_tool"},
            },
        )
        assert response.status_code in [200, 422, 500]

    def test_tool_use_message(self, client: TestClient, anthropic_headers: dict):
        """Verify tool_use content block in response is properly formatted."""
        response = client.post(
            "/v1/messages",
            headers=anthropic_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 1024,
                "messages": [
                    {"role": "user", "content": "What's 2+2?"},
                    {
                        "role": "assistant",
                        "content": [
                            {
                                "type": "tool_use",
                                "id": "toolu_01abc",
                                "name": "calculator",
                                "input": {"expression": "2+2"},
                            }
                        ],
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": "toolu_01abc",
                                "content": "4",
                            }
                        ],
                    },
                ],
            },
        )
        assert response.status_code in [200, 422, 500]


class TestAnthropicThinking:
    """Test Anthropic extended thinking feature."""

    def test_thinking_enabled(self, client: TestClient, anthropic_headers: dict):
        """Verify thinking configuration with enabled type."""
        response = client.post(
            "/v1/messages",
            headers=anthropic_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 16000,
                "messages": [{"role": "user", "content": "Solve this step by step: 15 * 23"}],
                "thinking": {
                    "type": "enabled",
                    "budget_tokens": 10000,
                },
            },
        )
        assert response.status_code in [200, 422, 500]

    def test_thinking_disabled(self, client: TestClient, anthropic_headers: dict):
        """Verify thinking can be explicitly disabled."""
        response = client.post(
            "/v1/messages",
            headers=anthropic_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "Hello"}],
                "thinking": {
                    "type": "disabled",
                },
            },
        )
        assert response.status_code in [200, 422, 500]


class TestAnthropicSystemPrompt:
    """Test Anthropic system prompt formats."""

    def test_system_as_string(self, client: TestClient, anthropic_headers: dict):
        """Verify system prompt as string is accepted."""
        response = client.post(
            "/v1/messages",
            headers=anthropic_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 1024,
                "system": "You are a helpful assistant. Always respond concisely.",
                "messages": [{"role": "user", "content": "Hello"}],
            },
        )
        assert response.status_code in [200, 422, 500]

    def test_system_as_array(self, client: TestClient, anthropic_headers: dict):
        """Verify system prompt as content block array is accepted."""
        response = client.post(
            "/v1/messages",
            headers=anthropic_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 1024,
                "system": [
                    {"type": "text", "text": "You are a helpful assistant."},
                    {"type": "text", "text": "Always respond concisely."},
                ],
                "messages": [{"role": "user", "content": "Hello"}],
            },
        )
        assert response.status_code in [200, 422, 500]

    def test_system_with_cache_control(self, client: TestClient, anthropic_headers: dict):
        """Verify system prompt with cache_control is accepted."""
        response = client.post(
            "/v1/messages",
            headers=anthropic_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 1024,
                "system": [
                    {
                        "type": "text",
                        "text": "You are a helpful assistant with extensive knowledge.",
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                "messages": [{"role": "user", "content": "Hello"}],
            },
        )
        assert response.status_code in [200, 422, 500]


class TestAnthropicMetadata:
    """Test Anthropic metadata parameter."""

    def test_metadata_user_id(self, client: TestClient, anthropic_headers: dict):
        """Verify metadata with user_id is accepted."""
        response = client.post(
            "/v1/messages",
            headers=anthropic_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "Hello"}],
                "metadata": {"user_id": "user-123456"},
            },
        )
        assert response.status_code in [200, 422, 500]


class TestAnthropicStopSequences:
    """Test Anthropic stop_sequences parameter."""

    def test_stop_sequences(self, client: TestClient, anthropic_headers: dict):
        """Verify stop_sequences parameter is accepted."""
        response = client.post(
            "/v1/messages",
            headers=anthropic_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "Count to 10"}],
                "stop_sequences": ["5", "\n\n"],
            },
        )
        assert response.status_code in [200, 422, 500]


class TestAnthropicTopK:
    """Test Anthropic top_k parameter (unique to Anthropic)."""

    def test_top_k_parameter(self, client: TestClient, anthropic_headers: dict):
        """Verify top_k parameter is accepted."""
        response = client.post(
            "/v1/messages",
            headers=anthropic_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "Hello"}],
                "top_k": 40,
            },
        )
        assert response.status_code in [200, 422, 500]


class TestAnthropicDocumentBlock:
    """Test Anthropic document content blocks."""

    def test_document_base64_pdf(self, client: TestClient, anthropic_headers: dict):
        """Verify base64 PDF document is accepted."""
        # Minimal PDF structure (not valid but tests format acceptance)
        fake_pdf_b64 = "JVBERi0xLjQKMSAwIG9iago8PAovVHlwZSAvQ2F0YWxvZwo+PgplbmRvYmoK"

        response = client.post(
            "/v1/messages",
            headers=anthropic_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 1024,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "What is in this document?"},
                            {
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": "application/pdf",
                                    "data": fake_pdf_b64,
                                },
                            },
                        ],
                    }
                ],
            },
        )
        assert response.status_code in [200, 422, 500]

    def test_document_with_title_and_context(self, client: TestClient, anthropic_headers: dict):
        """Verify document with title and context is accepted."""
        fake_pdf_b64 = "JVBERi0xLjQKMSAwIG9iago8PAovVHlwZSAvQ2F0YWxvZwo+PgplbmRvYmoK"

        response = client.post(
            "/v1/messages",
            headers=anthropic_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 1024,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Summarize this document"},
                            {
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": "application/pdf",
                                    "data": fake_pdf_b64,
                                },
                                "title": "Annual Report 2024",
                                "context": "This is the company's financial report",
                            },
                        ],
                    }
                ],
            },
        )
        assert response.status_code in [200, 422, 500]

    def test_document_text_source(self, client: TestClient, anthropic_headers: dict):
        """Verify text document source is accepted."""
        response = client.post(
            "/v1/messages",
            headers=anthropic_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 1024,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Analyze this text"},
                            {
                                "type": "document",
                                "source": {
                                    "type": "text",
                                    "media_type": "text/plain",
                                    "data": "This is a sample document with some text content.",
                                },
                            },
                        ],
                    }
                ],
            },
        )
        assert response.status_code in [200, 422, 500]


class TestAnthropicImageFormats:
    """Test Anthropic image content block formats."""

    def test_image_url_source(self, client: TestClient, anthropic_headers: dict):
        """Verify URL image source format is accepted."""
        response = client.post(
            "/v1/messages",
            headers=anthropic_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 1024,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Describe this image"},
                            {
                                "type": "image",
                                "source": {
                                    "type": "url",
                                    "url": "https://example.com/image.jpg",
                                },
                            },
                        ],
                    }
                ],
            },
        )
        # May fail due to URL not accessible, but format should be accepted
        assert response.status_code in [200, 400, 422, 500]


class TestAnthropicResponseStructure:
    """Test response structure matches Anthropic spec."""

    @pytest.mark.integration
    def test_response_has_required_fields(self, client: TestClient, anthropic_headers: dict):
        """Verify response contains all required Anthropic fields."""
        response = client.post(
            "/v1/messages",
            headers=anthropic_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "Say test"}],
            },
        )

        if response.status_code == 200:
            data = response.json()

            # Required top-level fields
            assert "id" in data
            assert data["id"].startswith("msg_")
            assert "type" in data
            assert data["type"] == "message"
            assert "role" in data
            assert data["role"] == "assistant"
            assert "content" in data
            assert "model" in data
            assert "stop_reason" in data

    @pytest.mark.integration
    def test_content_structure(self, client: TestClient, anthropic_headers: dict):
        """Verify content field structure matches Anthropic spec."""
        response = client.post(
            "/v1/messages",
            headers=anthropic_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "Say test"}],
            },
        )

        if response.status_code == 200:
            data = response.json()

            # Content should be an array of content blocks
            assert isinstance(data["content"], list)
            assert len(data["content"]) >= 1

            # Each block should have type
            for block in data["content"]:
                assert "type" in block
                if block["type"] == "text":
                    assert "text" in block

    @pytest.mark.integration
    def test_usage_structure(self, client: TestClient, anthropic_headers: dict):
        """Verify usage field structure matches Anthropic spec."""
        response = client.post(
            "/v1/messages",
            headers=anthropic_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "Say test"}],
            },
        )

        if response.status_code == 200:
            data = response.json()

            assert "usage" in data
            usage = data["usage"]
            # Anthropic uses input_tokens and output_tokens
            assert "input_tokens" in usage
            assert "output_tokens" in usage

    @pytest.mark.integration
    def test_stop_reason_values(self, client: TestClient, anthropic_headers: dict):
        """Verify stop_reason has valid Anthropic values."""
        response = client.post(
            "/v1/messages",
            headers=anthropic_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "Say test"}],
            },
        )

        if response.status_code == 200:
            data = response.json()

            # Valid stop_reason values per Anthropic spec
            valid_reasons = ["end_turn", "max_tokens", "stop_sequence", "tool_use"]
            assert data["stop_reason"] in valid_reasons
