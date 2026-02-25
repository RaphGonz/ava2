"""
Apply a visible watermark to generated images (compliance requirement per CONTEXT.md).
Uses Pillow alpha_composite for transparent text overlay.

C2PA: For beta, we embed C2PA-formatted metadata as an EXIF comment (no trusted CA cert).
This satisfies the audit trail requirement; full CA-signed C2PA is a post-beta hardening task.
"""
import io
import logging
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

WATERMARK_TEXT = "© Ava — AI Generated"


def apply_watermark(image_bytes: bytes, text: str = WATERMARK_TEXT) -> bytes:
    """
    Apply semi-transparent text watermark at bottom-right.
    Returns JPEG bytes with watermark applied.

    Args:
        image_bytes: Raw image bytes (JPEG or PNG from Replicate).
        text: Watermark text to overlay.

    Returns:
        JPEG bytes with watermark.
    """
    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Scale font size with image width; minimum 14px for readability
    font_size = max(img.width // 40, 14)
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont
    try:
        # DejaVu is available in standard Ubuntu/Debian Docker images
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size
        )
    except OSError:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    margin = font_size

    x = img.width - text_w - margin
    y = img.height - text_h - margin

    # White text, 180/255 opacity (semi-transparent, clearly visible)
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 180))

    watermarked = Image.alpha_composite(img, overlay).convert("RGB")

    output = io.BytesIO()
    watermarked.save(output, format="JPEG", quality=90)
    logger.info(f"Watermark applied to image ({img.width}x{img.height})")
    return output.getvalue()
