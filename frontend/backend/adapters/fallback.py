"""Fallback adapter — provides frames when video generation is blocked.

Generates frames from the actual source image with zoom/pan effects
to simulate an exploded-view animation.
"""

import base64
import io
import logging
import os

from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)


def _load_source_image(image_url: str) -> Image.Image | None:
    """Load the source image from a file path or file:// URL."""
    path = image_url.replace("file://", "")
    if not os.path.exists(path):
        logger.warning("Fallback: source image not found at %s", path)
        return None
    try:
        return Image.open(path).convert("RGB")
    except Exception as e:
        logger.warning("Fallback: could not load source image — %s", e)
        return None


def generate_placeholder_frames(count: int = 24, mode: str = "turntable", image_url: str = "") -> list[str]:
    """Generate frame data URIs for the slider.

    If image_url is provided, creates zoom/pan frames from the actual image.
    Otherwise falls back to gradient placeholders.
    """
    source_img = _load_source_image(image_url) if image_url else None

    if source_img is None:
        return _generate_gradient_frames(count, mode)

    frames = []
    # Resize source to a reasonable working size
    max_dim = 640
    if source_img.width > max_dim or source_img.height > max_dim:
        ratio = max_dim / max(source_img.width, source_img.height)
        source_img = source_img.resize(
            (int(source_img.width * ratio), int(source_img.height * ratio)),
            Image.LANCZOS,
        )

    target_w, target_h = 640, 480
    for i in range(count):
        progress = i / max(count - 1, 1)

        if mode == "explode":
            # Zoom out from 100% to 70% and add vertical separation lines
            scale = 1.0 - progress * 0.3
            sw = int(source_img.width * scale)
            sh = int(source_img.height * scale)
            scaled = source_img.resize((sw, sh), Image.LANCZOS)

            frame = Image.new("RGB", (target_w, target_h), (30, 30, 35))
            # Center the scaled image, shift up/down based on progress
            offset_x = (target_w - sw) // 2
            offset_y = (target_h - sh) // 2 - int(progress * 30)
            frame.paste(scaled, (offset_x, offset_y))

            # Draw separation lines between "parts" as progress increases
            if progress > 0.1:
                draw = ImageDraw.Draw(frame, "RGBA")
                num_splits = 3
                for s in range(1, num_splits + 1):
                    gap_y = offset_y + int(sh * s / (num_splits + 1)) + int(progress * 15 * s)
                    if 0 < gap_y < target_h:
                        draw.line(
                            [(offset_x - 5, gap_y), (offset_x + sw + 5, gap_y)],
                            fill=(58, 216, 255, int(180 * progress)),
                            width=2,
                        )
        else:
            # Turntable: rotate the image by shifting horizontally (fake rotation)
            shift = int(progress * source_img.width * 0.3)
            frame = Image.new("RGB", (target_w, target_h), (30, 30, 35))
            # Paste shifted copies to simulate rotation
            paste_x = (target_w - source_img.width) // 2 - shift
            frame.paste(source_img, (paste_x, (target_h - source_img.height) // 2))
            # Mirror edge for wrap-around effect
            if paste_x + source_img.width > target_w:
                overflow = paste_x + source_img.width - target_w
                mirrored = source_img.transpose(Image.FLIP_LEFT_RIGHT)
                frame.paste(mirrored.crop((0, 0, overflow, source_img.height)), (0, (target_h - source_img.height) // 2))

        # Encode as JPEG data URI
        buf = io.BytesIO()
        frame.save(buf, format="JPEG", quality=85)
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        frames.append(f"data:image/jpeg;base64,{b64}")

    logger.info("Fallback: generated %d image-based frames for %s", count, mode)
    return frames


def _generate_gradient_frames(count: int = 24, mode: str = "turntable") -> list[str]:
    """Generate gradient placeholder frames (used when no source image available)."""
    frames = []
    for i in range(count):
        progress = i / max(count - 1, 1)
        hue = int(progress * 360)
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="640" height="480" viewBox="0 0 640 480">
<defs>
<linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
<stop offset="0%" style="stop-color:hsl({hue},40%,80%)"/>
<stop offset="100%" style="stop-color:hsl({hue + 60},40%,60%)"/>
</linearGradient>
</defs>
<rect width="640" height="480" fill="url(#g)"/>
<circle cx="320" cy="240" r="120" fill="rgba(255,255,255,0.3)" stroke="rgba(0,0,0,0.2)" stroke-width="2"/>
<text x="320" y="250" text-anchor="middle" font-family="sans-serif" font-size="16" fill="rgba(0,0,0,0.5)">
{mode} — frame {i + 1}/{count}
</text>
</svg>"""
        encoded = base64.b64encode(svg.encode()).decode()
        frames.append(f"data:image/svg+xml;base64,{encoded}")

    logger.info("Fallback: generated %d gradient placeholder frames for %s", count, mode)
    return frames
