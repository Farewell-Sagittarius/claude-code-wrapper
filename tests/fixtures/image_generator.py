"""Generate test images using Pillow for multimodal testing."""

import base64
import io
from typing import Tuple

from PIL import Image, ImageDraw, ImageFont


class TestImageGenerator:
    """Test image generator for multimodal tests."""

    @staticmethod
    def create_color_blocks(width: int = 200, height: int = 200) -> bytes:
        """Create image with four color blocks (red, green, blue, yellow).

        Used for testing color recognition.
        """
        img = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(img)

        half_w, half_h = width // 2, height // 2

        # Four quadrants with distinct colors
        draw.rectangle([0, 0, half_w, half_h], fill="red")
        draw.rectangle([half_w, 0, width, half_h], fill="green")
        draw.rectangle([0, half_h, half_w, height], fill="blue")
        draw.rectangle([half_w, half_h, width, height], fill="yellow")

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    @staticmethod
    def create_text_image(
        text: str,
        width: int = 400,
        height: int = 100,
        font_size: int = 24,
    ) -> bytes:
        """Create image containing specified text.

        Used for OCR/text recognition testing.
        """
        img = Image.new("RGB", (width, height), color="white")
        draw = ImageDraw.Draw(img)

        # Try to use a basic font, fall back to default
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
        except (OSError, IOError):
            font = ImageFont.load_default()

        # Center the text
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) // 2
        y = (height - text_height) // 2

        draw.text((x, y), text, fill="black", font=font)

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    @staticmethod
    def create_code_screenshot(width: int = 800, height: int = 400) -> bytes:
        """Create simulated code editor screenshot.

        Dark background with syntax-highlighted code appearance.
        """
        bg_color = "#1e1e1e"
        text_color = "#d4d4d4"
        keyword_color = "#569cd6"
        string_color = "#ce9178"
        comment_color = "#6a9955"

        img = Image.new("RGB", (width, height), color=bg_color)
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 14)
        except (OSError, IOError):
            font = ImageFont.load_default()

        # Simulated code lines with different colors
        lines = [
            (comment_color, "# Python example"),
            (text_color, ""),
            (keyword_color, "def"),
            (text_color, " hello_world():"),
            (text_color, "    "),
            (keyword_color, "print"),
            (text_color, "("),
            (string_color, "'Hello, World!'"),
            (text_color, ")"),
            (text_color, ""),
            (keyword_color, "if"),
            (text_color, " __name__ == "),
            (string_color, "'__main__'"),
            (text_color, ":"),
            (text_color, "    hello_world()"),
        ]

        # Render as simple lines (simplified for readability)
        code_text = [
            "# Python example",
            "",
            "def hello_world():",
            "    print('Hello, World!')",
            "",
            "if __name__ == '__main__':",
            "    hello_world()",
        ]

        y = 20
        line_height = 22
        for line in code_text:
            draw.text((20, y), line, fill=text_color, font=font)
            y += line_height

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    @staticmethod
    def create_diagram(width: int = 600, height: int = 300) -> bytes:
        """Create simple flowchart diagram.

        Shows Input -> Process -> Output flow.
        """
        img = Image.new("RGB", (width, height), color="white")
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        except (OSError, IOError):
            font = ImageFont.load_default()

        box_color = "#333333"
        arrow_color = "#666666"

        # Box positions: (x1, y1, x2, y2, label)
        boxes = [
            (50, 100, 150, 160, "Input"),
            (250, 100, 350, 160, "Process"),
            (450, 100, 550, 160, "Output"),
        ]

        # Draw boxes
        for x1, y1, x2, y2, label in boxes:
            draw.rectangle([x1, y1, x2, y2], outline=box_color, width=2)
            # Center label
            bbox = draw.textbbox((0, 0), label, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            tx = x1 + (x2 - x1 - text_w) // 2
            ty = y1 + (y2 - y1 - text_h) // 2
            draw.text((tx, ty), label, fill=box_color, font=font)

        # Draw arrows
        arrow_y = 130

        # Arrow 1: Input -> Process
        draw.line([(150, arrow_y), (240, arrow_y)], fill=arrow_color, width=2)
        draw.polygon([(250, arrow_y), (240, arrow_y - 5), (240, arrow_y + 5)], fill=arrow_color)

        # Arrow 2: Process -> Output
        draw.line([(350, arrow_y), (440, arrow_y)], fill=arrow_color, width=2)
        draw.polygon([(450, arrow_y), (440, arrow_y - 5), (440, arrow_y + 5)], fill=arrow_color)

        # Title
        draw.text((220, 30), "Simple Flowchart", fill=box_color, font=font)

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    @staticmethod
    def create_shapes(width: int = 400, height: int = 300) -> bytes:
        """Create image with various geometric shapes.

        Circle, rectangle, triangle for shape recognition testing.
        """
        img = Image.new("RGB", (width, height), color="white")
        draw = ImageDraw.Draw(img)

        # Red circle
        draw.ellipse([30, 80, 130, 180], fill="red", outline="darkred", width=2)

        # Blue rectangle
        draw.rectangle([160, 80, 260, 180], fill="blue", outline="darkblue", width=2)

        # Green triangle
        triangle_points = [(345, 180), (295, 80), (395, 80)]
        draw.polygon(triangle_points, fill="green", outline="darkgreen")

        # Labels
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except (OSError, IOError):
            font = ImageFont.load_default()

        draw.text((55, 200), "Circle", fill="black", font=font)
        draw.text((180, 200), "Rectangle", fill="black", font=font)
        draw.text((315, 200), "Triangle", fill="black", font=font)

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    @staticmethod
    def create_large_image(width: int = 3000, height: int = 2000) -> bytes:
        """Create large image for testing size limits.

        May need compression or rejection handling.
        """
        img = Image.new("RGB", (width, height), color="#f0f0f0")
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)
        except (OSError, IOError):
            font = ImageFont.load_default()

        text = f"Large Image: {width}x{height}"
        draw.text((100, 100), text, fill="#333333", font=font)

        # Add some patterns for visual interest
        for i in range(0, width, 200):
            draw.line([(i, 0), (i, height)], fill="#ddd", width=1)
        for i in range(0, height, 200):
            draw.line([(0, i), (width, i)], fill="#ddd", width=1)

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    @staticmethod
    def create_transparent_image(width: int = 200, height: int = 200) -> bytes:
        """Create PNG with transparency (alpha channel).

        Red circle on transparent background.
        """
        img = Image.new("RGBA", (width, height), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Red circle with full opacity
        margin = 20
        draw.ellipse(
            [margin, margin, width - margin, height - margin],
            fill=(255, 0, 0, 255),
            outline=(128, 0, 0, 255),
        )

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    @staticmethod
    def create_jpeg_image(width: int = 400, height: int = 300, quality: int = 85) -> bytes:
        """Create JPEG format image.

        For testing JPEG format handling.
        """
        img = Image.new("RGB", (width, height), color="#87CEEB")  # Sky blue
        draw = ImageDraw.Draw(img)

        # Simple landscape
        draw.rectangle([0, height // 2, width, height], fill="#228B22")  # Green grass
        draw.ellipse([width - 100, 30, width - 30, 100], fill="#FFD700")  # Yellow sun

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality)
        return buffer.getvalue()

    @staticmethod
    def create_webp_image(width: int = 400, height: int = 300) -> bytes:
        """Create WebP format image.

        For testing WebP format handling.
        """
        img = Image.new("RGB", (width, height), color="#E6E6FA")  # Lavender
        draw = ImageDraw.Draw(img)

        # Abstract pattern
        for i in range(0, width, 50):
            draw.rectangle([i, 0, i + 25, height], fill="#9370DB")

        buffer = io.BytesIO()
        img.save(buffer, format="WEBP", quality=85)
        return buffer.getvalue()

    @staticmethod
    def to_base64(image_bytes: bytes) -> str:
        """Convert image bytes to base64 string."""
        return base64.b64encode(image_bytes).decode("utf-8")

    @staticmethod
    def to_data_url(image_bytes: bytes, media_type: str = "image/png") -> str:
        """Convert image bytes to data URL."""
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        return f"data:{media_type};base64,{b64}"
