"""Tests for real multimodal functionality using generated images.

Uses Pillow-generated test images to verify actual image processing
rather than just format validation.
"""

import pytest
from fastapi.testclient import TestClient

from .fixtures.image_generator import TestImageGenerator


@pytest.fixture
def image_gen():
    """Provide image generator instance."""
    return TestImageGenerator()


class TestOpenAIRealImages:
    """Test real image processing with OpenAI format."""

    @pytest.mark.integration
    def test_color_recognition(self, client: TestClient, basic_headers: dict, image_gen):
        """Verify model can recognize colors in color block image."""
        img_bytes = image_gen.create_color_blocks()
        img_url = image_gen.to_data_url(img_bytes, "image/png")

        response = client.post(
            "/v1/chat/completions",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "What colors do you see in this image? List them.",
                            },
                            {"type": "image_url", "image_url": {"url": img_url}},
                        ],
                    }
                ],
            },
        )

        assert response.status_code == 200
        content = response.json()["choices"][0]["message"]["content"].lower()
        # Should recognize at least some of the colors
        colors_found = sum(1 for c in ["red", "green", "blue", "yellow"] if c in content)
        assert colors_found >= 2, f"Expected at least 2 colors, found in: {content}"

    @pytest.mark.integration
    def test_text_recognition(self, client: TestClient, basic_headers: dict, image_gen):
        """Verify model can read text from image (OCR)."""
        test_text = "Hello Claude"
        img_bytes = image_gen.create_text_image(test_text)
        img_url = image_gen.to_data_url(img_bytes, "image/png")

        response = client.post(
            "/v1/chat/completions",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "What text is written in this image?"},
                            {"type": "image_url", "image_url": {"url": img_url}},
                        ],
                    }
                ],
            },
        )

        assert response.status_code == 200
        content = response.json()["choices"][0]["message"]["content"].lower()
        # Should recognize at least part of the text
        assert "hello" in content or "claude" in content, f"Text not found in: {content}"

    @pytest.mark.integration
    def test_code_screenshot_understanding(self, client: TestClient, basic_headers: dict, image_gen):
        """Verify model can understand code in screenshot."""
        img_bytes = image_gen.create_code_screenshot()
        img_url = image_gen.to_data_url(img_bytes, "image/png")

        response = client.post(
            "/v1/chat/completions",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "What programming language is shown? What does the code do?",
                            },
                            {"type": "image_url", "image_url": {"url": img_url}},
                        ],
                    }
                ],
            },
        )

        assert response.status_code == 200
        content = response.json()["choices"][0]["message"]["content"].lower()
        # Should recognize Python and hello world
        assert "python" in content or "hello" in content, f"Code not recognized: {content}"

    @pytest.mark.integration
    def test_diagram_understanding(self, client: TestClient, basic_headers: dict, image_gen):
        """Verify model can understand flowchart diagram."""
        img_bytes = image_gen.create_diagram()
        img_url = image_gen.to_data_url(img_bytes, "image/png")

        response = client.post(
            "/v1/chat/completions",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Describe this diagram. What does it show?"},
                            {"type": "image_url", "image_url": {"url": img_url}},
                        ],
                    }
                ],
            },
        )

        assert response.status_code == 200
        content = response.json()["choices"][0]["message"]["content"].lower()
        # Should recognize flowchart elements
        terms = ["input", "process", "output", "flow", "diagram", "arrow"]
        found = sum(1 for t in terms if t in content)
        assert found >= 2, f"Diagram not understood: {content}"

    @pytest.mark.integration
    def test_shape_recognition(self, client: TestClient, basic_headers: dict, image_gen):
        """Verify model can recognize geometric shapes."""
        img_bytes = image_gen.create_shapes()
        img_url = image_gen.to_data_url(img_bytes, "image/png")

        response = client.post(
            "/v1/chat/completions",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "What shapes do you see in this image?"},
                            {"type": "image_url", "image_url": {"url": img_url}},
                        ],
                    }
                ],
            },
        )

        assert response.status_code == 200
        content = response.json()["choices"][0]["message"]["content"].lower()
        # Should recognize shapes
        shapes = ["circle", "rectangle", "square", "triangle"]
        found = sum(1 for s in shapes if s in content)
        assert found >= 2, f"Shapes not recognized: {content}"


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


class TestImageFormats:
    """Test different image format handling."""

    @pytest.mark.integration
    def test_jpeg_format(self, client: TestClient, basic_headers: dict, image_gen):
        """Verify JPEG format images are processed correctly."""
        img_bytes = image_gen.create_jpeg_image()
        img_url = image_gen.to_data_url(img_bytes, "image/jpeg")

        response = client.post(
            "/v1/chat/completions",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Describe this image briefly."},
                            {"type": "image_url", "image_url": {"url": img_url}},
                        ],
                    }
                ],
            },
        )

        assert response.status_code == 200
        content = response.json()["choices"][0]["message"]["content"]
        assert len(content) > 10, "Expected meaningful description"

    @pytest.mark.integration
    def test_webp_format(self, client: TestClient, basic_headers: dict, image_gen):
        """Verify WebP format images are processed correctly."""
        img_bytes = image_gen.create_webp_image()
        img_url = image_gen.to_data_url(img_bytes, "image/webp")

        response = client.post(
            "/v1/chat/completions",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Describe this image briefly."},
                            {"type": "image_url", "image_url": {"url": img_url}},
                        ],
                    }
                ],
            },
        )

        assert response.status_code == 200
        content = response.json()["choices"][0]["message"]["content"]
        assert len(content) > 10, "Expected meaningful description"

    @pytest.mark.integration
    def test_png_with_transparency(self, client: TestClient, basic_headers: dict, image_gen):
        """Verify PNG with alpha channel is processed correctly."""
        img_bytes = image_gen.create_transparent_image()
        img_url = image_gen.to_data_url(img_bytes, "image/png")

        response = client.post(
            "/v1/chat/completions",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "What do you see in this image?"},
                            {"type": "image_url", "image_url": {"url": img_url}},
                        ],
                    }
                ],
            },
        )

        assert response.status_code == 200
        content = response.json()["choices"][0]["message"]["content"].lower()
        # Should see a red circle
        assert "red" in content or "circle" in content, f"Shape not recognized: {content}"


class TestLargeImages:
    """Test handling of large images."""

    @pytest.mark.integration
    def test_large_image_handling(self, client: TestClient, basic_headers: dict, image_gen):
        """Verify large images are handled (may compress or reject)."""
        img_bytes = image_gen.create_large_image()
        img_url = image_gen.to_data_url(img_bytes, "image/png")

        response = client.post(
            "/v1/chat/completions",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "What do you see in this image?"},
                            {"type": "image_url", "image_url": {"url": img_url}},
                        ],
                    }
                ],
            },
        )

        # Should either process successfully or return appropriate error
        assert response.status_code in [200, 400, 413, 422, 500]


class TestMultipleImages:
    """Test handling of multiple images in single request."""

    @pytest.mark.integration
    def test_compare_two_images(self, client: TestClient, basic_headers: dict, image_gen):
        """Verify model can compare two images."""
        colors_img = image_gen.create_color_blocks()
        shapes_img = image_gen.create_shapes()

        response = client.post(
            "/v1/chat/completions",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Compare these two images. What's different?"},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_gen.to_data_url(colors_img, "image/png")
                                },
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_gen.to_data_url(shapes_img, "image/png")
                                },
                            },
                        ],
                    }
                ],
            },
        )

        assert response.status_code == 200
        content = response.json()["choices"][0]["message"]["content"]
        assert len(content) > 20, "Expected comparison description"

    @pytest.mark.integration
    def test_anthropic_multiple_images(self, client: TestClient, anthropic_headers: dict, image_gen):
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


class TestImageDetail:
    """Test OpenAI detail parameter for images."""

    @pytest.mark.integration
    def test_detail_low(self, client: TestClient, basic_headers: dict, image_gen):
        """Verify detail='low' is accepted."""
        img_bytes = image_gen.create_color_blocks()
        img_url = image_gen.to_data_url(img_bytes, "image/png")

        response = client.post(
            "/v1/chat/completions",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "What do you see?"},
                            {"type": "image_url", "image_url": {"url": img_url, "detail": "low"}},
                        ],
                    }
                ],
            },
        )

        assert response.status_code == 200

    @pytest.mark.integration
    def test_detail_high(self, client: TestClient, basic_headers: dict, image_gen):
        """Verify detail='high' is accepted."""
        img_bytes = image_gen.create_text_image("High Detail Test")
        img_url = image_gen.to_data_url(img_bytes, "image/png")

        response = client.post(
            "/v1/chat/completions",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Read the text carefully."},
                            {"type": "image_url", "image_url": {"url": img_url, "detail": "high"}},
                        ],
                    }
                ],
            },
        )

        assert response.status_code == 200

    @pytest.mark.integration
    def test_detail_auto(self, client: TestClient, basic_headers: dict, image_gen):
        """Verify detail='auto' is accepted."""
        img_bytes = image_gen.create_shapes()
        img_url = image_gen.to_data_url(img_bytes, "image/png")

        response = client.post(
            "/v1/chat/completions",
            headers=basic_headers,
            json={
                "model": "claude-code-opus",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "What shapes do you see?"},
                            {"type": "image_url", "image_url": {"url": img_url, "detail": "auto"}},
                        ],
                    }
                ],
            },
        )

        assert response.status_code == 200
