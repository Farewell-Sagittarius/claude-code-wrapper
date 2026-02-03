"""Tests for multimodal (text + image) support in Anthropic format."""

import pytest
from fastapi.testclient import TestClient


# Small 1x1 PNG images for testing
RED_PIXEL_PNG = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
BLUE_PIXEL_PNG = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPj/HwADBwIAMCbHYQAAAABJRU5ErkJggg=="


class TestAnthropicMultimodal:
    """Test multimodal support in Anthropic format."""

    @pytest.mark.integration
    def test_text_block_array(self, client: TestClient, anthropic_headers: dict):
        """Text blocks in array format should work."""
        response = client.post(
            "/v1/messages",
            headers=anthropic_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 100,
                "messages": [
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": "Say 'test'"}],
                    }
                ],
            },
        )
        assert response.status_code == 200

    @pytest.mark.integration
    def test_anthropic_base64_image(self, client: TestClient, anthropic_headers: dict):
        """Anthropic format base64 image should be accepted."""
        response = client.post(
            "/v1/messages",
            headers=anthropic_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 100,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Describe this image"},
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": RED_PIXEL_PNG,
                                },
                            },
                        ],
                    }
                ],
            },
        )
        assert response.status_code == 200

    @pytest.mark.integration
    def test_mixed_text_and_images(self, client: TestClient, anthropic_headers: dict):
        """Mixed text and images should be processed."""
        response = client.post(
            "/v1/messages",
            headers=anthropic_headers,
            json={
                "model": "claude-code-opus",
                "max_tokens": 100,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "First image:"},
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": RED_PIXEL_PNG,
                                },
                            },
                            {"type": "text", "text": "Second image:"},
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": BLUE_PIXEL_PNG,
                                },
                            },
                            {"type": "text", "text": "Compare them."},
                        ],
                    }
                ],
            },
        )
        assert response.status_code == 200
