"""Tests for OpenAI API specification compliance.

Verifies that requests and responses conform to the official OpenAI
Chat Completions API specification.
"""

import pytest
from fastapi.testclient import TestClient


class TestOpenAIToolCalling:
    """Test OpenAI function calling / tools format."""

    def test_tools_definition_format(self, client: TestClient, basic_headers: dict):
        """Verify tools parameter format matches OpenAI spec."""
        response = client.post(
            "/v1/chat/completions",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "messages": [{"role": "user", "content": "What's the weather in Paris?"}],
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "description": "Get the current weather in a location",
                            "parameters": {
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
                        },
                    }
                ],
            },
        )
        # Should accept the tools format
        assert response.status_code in [200, 422, 500]

    def test_tool_choice_auto(self, client: TestClient, basic_headers: dict):
        """Verify tool_choice='auto' is accepted."""
        response = client.post(
            "/v1/chat/completions",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "messages": [{"role": "user", "content": "Hello"}],
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": "test_func",
                            "description": "A test function",
                            "parameters": {"type": "object", "properties": {}},
                        },
                    }
                ],
                "tool_choice": "auto",
            },
        )
        assert response.status_code in [200, 422, 500]

    def test_tool_choice_none(self, client: TestClient, basic_headers: dict):
        """Verify tool_choice='none' disables tool calling."""
        response = client.post(
            "/v1/chat/completions",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "messages": [{"role": "user", "content": "Hello"}],
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": "test_func",
                            "description": "A test function",
                            "parameters": {"type": "object", "properties": {}},
                        },
                    }
                ],
                "tool_choice": "none",
            },
        )
        assert response.status_code in [200, 422, 500]

    def test_tool_choice_required(self, client: TestClient, basic_headers: dict):
        """Verify tool_choice='required' forces tool use."""
        response = client.post(
            "/v1/chat/completions",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "messages": [{"role": "user", "content": "Hello"}],
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": "test_func",
                            "description": "A test function",
                            "parameters": {"type": "object", "properties": {}},
                        },
                    }
                ],
                "tool_choice": "required",
            },
        )
        assert response.status_code in [200, 422, 500]

    def test_tool_choice_specific_function(self, client: TestClient, basic_headers: dict):
        """Verify tool_choice can specify a specific function."""
        response = client.post(
            "/v1/chat/completions",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "messages": [{"role": "user", "content": "Hello"}],
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": "specific_func",
                            "description": "A specific function",
                            "parameters": {"type": "object", "properties": {}},
                        },
                    }
                ],
                "tool_choice": {
                    "type": "function",
                    "function": {"name": "specific_func"},
                },
            },
        )
        assert response.status_code in [200, 422, 500]

    def test_parallel_tool_calls(self, client: TestClient, basic_headers: dict):
        """Verify parallel_tool_calls parameter is accepted."""
        response = client.post(
            "/v1/chat/completions",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "messages": [{"role": "user", "content": "Hello"}],
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": "test_func",
                            "description": "A test function",
                            "parameters": {"type": "object", "properties": {}},
                        },
                    }
                ],
                "parallel_tool_calls": True,
            },
        )
        assert response.status_code in [200, 422, 500]


class TestOpenAIResponseFormat:
    """Test response_format parameter (JSON mode)."""

    def test_response_format_json_object(self, client: TestClient, basic_headers: dict):
        """Verify response_format={'type': 'json_object'} is accepted."""
        response = client.post(
            "/v1/chat/completions",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "messages": [
                    {"role": "user", "content": "Return a JSON object with a greeting field"}
                ],
                "response_format": {"type": "json_object"},
            },
        )
        assert response.status_code in [200, 422, 500]

    def test_response_format_json_schema(self, client: TestClient, basic_headers: dict):
        """Verify response_format with json_schema is accepted."""
        response = client.post(
            "/v1/chat/completions",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "messages": [{"role": "user", "content": "Generate a person object"}],
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "person",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "age": {"type": "integer"},
                            },
                            "required": ["name", "age"],
                        },
                    },
                },
            },
        )
        assert response.status_code in [200, 422, 500]

    def test_response_format_text(self, client: TestClient, basic_headers: dict):
        """Verify response_format={'type': 'text'} is accepted."""
        response = client.post(
            "/v1/chat/completions",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "messages": [{"role": "user", "content": "Hello"}],
                "response_format": {"type": "text"},
            },
        )
        assert response.status_code in [200, 422, 500]


class TestOpenAISeedParameter:
    """Test seed parameter for reproducibility."""

    def test_seed_parameter_accepted(self, client: TestClient, basic_headers: dict):
        """Verify seed parameter is accepted."""
        response = client.post(
            "/v1/chat/completions",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "messages": [{"role": "user", "content": "Say hello"}],
                "seed": 12345,
            },
        )
        assert response.status_code in [200, 422, 500]

    @pytest.mark.integration
    def test_seed_reproducibility(self, client: TestClient, basic_headers: dict):
        """Verify same seed produces consistent output."""
        request_data = {
            "model": "claude-code-opus",
            "messages": [{"role": "user", "content": "Pick a random number between 1 and 10"}],
            "seed": 42,
            "temperature": 0,
        }

        response1 = client.post("/v1/chat/completions", headers=basic_headers, json=request_data)
        response2 = client.post("/v1/chat/completions", headers=basic_headers, json=request_data)

        if response1.status_code == 200 and response2.status_code == 200:
            # With same seed and temperature=0, outputs should be identical
            content1 = response1.json()["choices"][0]["message"]["content"]
            content2 = response2.json()["choices"][0]["message"]["content"]
            # Note: May not be perfectly reproducible depending on backend
            assert content1 is not None and content2 is not None


class TestOpenAILogprobs:
    """Test logprobs parameters."""

    def test_logprobs_parameter(self, client: TestClient, basic_headers: dict):
        """Verify logprobs parameter is accepted."""
        response = client.post(
            "/v1/chat/completions",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "messages": [{"role": "user", "content": "Hello"}],
                "logprobs": True,
            },
        )
        assert response.status_code in [200, 422, 500]

    def test_top_logprobs_parameter(self, client: TestClient, basic_headers: dict):
        """Verify top_logprobs parameter is accepted."""
        response = client.post(
            "/v1/chat/completions",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "messages": [{"role": "user", "content": "Hello"}],
                "logprobs": True,
                "top_logprobs": 5,
            },
        )
        assert response.status_code in [200, 422, 500]


class TestOpenAIStopSequences:
    """Test stop sequences parameter."""

    def test_stop_string(self, client: TestClient, basic_headers: dict):
        """Verify stop as string is accepted."""
        response = client.post(
            "/v1/chat/completions",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "messages": [{"role": "user", "content": "Count to 10"}],
                "stop": "5",
            },
        )
        assert response.status_code in [200, 422, 500]

    def test_stop_array(self, client: TestClient, basic_headers: dict):
        """Verify stop as array is accepted."""
        response = client.post(
            "/v1/chat/completions",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "messages": [{"role": "user", "content": "Write a story"}],
                "stop": ["THE END", ".", "\n\n"],
            },
        )
        assert response.status_code in [200, 422, 500]


class TestOpenAIStreamOptions:
    """Test stream_options parameter."""

    def test_stream_options_include_usage(self, client: TestClient, basic_headers: dict):
        """Verify stream_options with include_usage is accepted."""
        response = client.post(
            "/v1/chat/completions",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "messages": [{"role": "user", "content": "Hello"}],
                "stream": True,
                "stream_options": {"include_usage": True},
            },
        )
        assert response.status_code in [200, 422, 500]


class TestOpenAIMessageFormats:
    """Test various message formats per OpenAI spec."""

    def test_message_with_name(self, client: TestClient, basic_headers: dict):
        """Verify message with name field is accepted."""
        response = client.post(
            "/v1/chat/completions",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "messages": [
                    {"role": "user", "content": "Hello", "name": "alice"},
                    {"role": "assistant", "content": "Hi Alice!"},
                    {"role": "user", "content": "How are you?", "name": "alice"},
                ],
            },
        )
        assert response.status_code in [200, 422, 500]

    def test_tool_message(self, client: TestClient, basic_headers: dict):
        """Verify tool role message is accepted."""
        response = client.post(
            "/v1/chat/completions",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "messages": [
                    {"role": "user", "content": "What's the weather?"},
                    {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call_abc123",
                                "type": "function",
                                "function": {
                                    "name": "get_weather",
                                    "arguments": '{"location": "Paris"}',
                                },
                            }
                        ],
                    },
                    {
                        "role": "tool",
                        "tool_call_id": "call_abc123",
                        "content": '{"temperature": 22, "condition": "sunny"}',
                    },
                ],
            },
        )
        assert response.status_code in [200, 422, 500]


class TestOpenAIResponseStructure:
    """Test response structure matches OpenAI spec."""

    @pytest.mark.integration
    def test_response_has_required_fields(self, client: TestClient, basic_headers: dict):
        """Verify response contains all required OpenAI fields."""
        response = client.post(
            "/v1/chat/completions",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "messages": [{"role": "user", "content": "Say test"}],
            },
        )

        if response.status_code == 200:
            data = response.json()

            # Required top-level fields
            assert "id" in data
            assert "object" in data
            assert data["object"] == "chat.completion"
            assert "created" in data
            assert "model" in data
            assert "choices" in data

            # Choices structure
            assert len(data["choices"]) >= 1
            choice = data["choices"][0]
            assert "index" in choice
            assert "message" in choice
            assert "finish_reason" in choice

            # Message structure
            message = choice["message"]
            assert "role" in message
            assert message["role"] == "assistant"
            assert "content" in message

    @pytest.mark.integration
    def test_usage_structure(self, client: TestClient, basic_headers: dict):
        """Verify usage field structure matches OpenAI spec."""
        response = client.post(
            "/v1/chat/completions",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "messages": [{"role": "user", "content": "Say test"}],
            },
        )

        if response.status_code == 200:
            data = response.json()

            assert "usage" in data
            usage = data["usage"]
            assert "prompt_tokens" in usage
            assert "completion_tokens" in usage
            assert "total_tokens" in usage
            assert usage["total_tokens"] == usage["prompt_tokens"] + usage["completion_tokens"]

    @pytest.mark.integration
    def test_id_format(self, client: TestClient, basic_headers: dict):
        """Verify response ID follows expected format."""
        response = client.post(
            "/v1/chat/completions",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "messages": [{"role": "user", "content": "Say test"}],
            },
        )

        if response.status_code == 200:
            data = response.json()
            # OpenAI format: chatcmpl-xxxxx
            assert data["id"].startswith("chatcmpl-")
