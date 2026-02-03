"""Tests for real multimodal functionality using generated images.

Uses Pillow-generated test images to verify actual image processing
with Anthropic format.
"""

import pytest
from fastapi.testclient import TestClient

from .fixtures.image_generator import TestImageGenerator


@pytest.fixture
def image_gen():
    """Provide image generator instance."""
    return TestImageGenerator()


class TestAnthropicRealImages:
    """Test real image processing with Anthropic format."""

    @pytest.mark.integration
    def test_color_recognition(self, client: TestClient, anthropic_headers: dict, image_gen):
        """Verify model can recognize colors using Anthropic format."""
        img_bytes = image_gen.create_color_blocks()
        img_b64 = image_gen.to_base64(img_bytes)

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
                            {"type": "text", "text": "List all colors you see in this image."},
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": img_b64,
                                },
                            },
                        ],
                    }
                ],
            },
        )

        assert response.status_code == 200
        content = response.json()["content"][0]["text"].lower()
        colors_found = sum(1 for c in ["red", "green", "blue", "yellow"] if c in content)
        assert colors_found >= 2, f"Expected colors, found: {content}"

    @pytest.mark.integration
    def test_text_recognition(self, client: TestClient, anthropic_headers: dict, image_gen):
        """Verify model can read text using Anthropic format."""
        test_text = "Anthropic Test"
        img_bytes = image_gen.create_text_image(test_text)
        img_b64 = image_gen.to_base64(img_bytes)

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
                            {"type": "text", "text": "Read the text in this image."},
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": img_b64,
                                },
                            },
                        ],
                    }
                ],
            },
        )

        assert response.status_code == 200
        content = response.json()["content"][0]["text"].lower()
        assert "anthropic" in content or "test" in content, f"Text not found: {content}"

    @pytest.mark.integration
    def test_multiple_images(self, client: TestClient, anthropic_headers: dict, image_gen):
        """Verify Anthropic format handles multiple images."""
        colors_img = image_gen.create_color_blocks()
        text_img = image_gen.create_text_image("Image 2")

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
                            {"type": "text", "text": "First image:"},
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_gen.to_base64(colors_img),
                                },
                            },
                            {"type": "text", "text": "Second image:"},
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_gen.to_base64(text_img),
                                },
                            },
                            {"type": "text", "text": "Describe both images."},
                        ],
                    }
                ],
            },
        )

        assert response.status_code == 200
