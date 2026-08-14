"""Cross-platform Pillow primitives for CONTENT AGENT slide rendering."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Sequence

from PIL import Image, ImageDraw, ImageFont

try:
    from .project_paths import FONTS_DIR
except ImportError:  # Direct execution from scripts/.
    from project_paths import FONTS_DIR


SLIDE_SIZE = (1080, 1350)
JPEG_QUALITY = 95

FONT_FILES = {
    "display": FONTS_DIR / "Oswald-Variable.ttf",
    "body": FONTS_DIR / "Rubik-Variable.ttf",
}


def font_path(role: str) -> Path:
    """Return a bundled OFL font and reject undeclared system-font fallbacks."""

    try:
        path = FONT_FILES[role]
    except KeyError as exc:
        raise ValueError(f"Unknown font role: {role!r}") from exc
    if not path.is_file():
        raise FileNotFoundError(f"Bundled font is missing: {path}")
    return path


def load_font(role: str, size: int, weight: int | None = None) -> ImageFont.FreeTypeFont:
    """Load a bundled variable font at a requested weight."""

    font = ImageFont.truetype(str(font_path(role)), size=size)
    if weight is not None:
        axes = font.get_variation_axes()
        if axes:
            minimum = int(axes[0]["minimum"])
            maximum = int(axes[0]["maximum"])
            font.set_variation_by_axes([max(minimum, min(maximum, int(weight)))])
    return font


def new_slide(background: tuple[int, int, int] = (18, 20, 22)) -> Image.Image:
    """Create an RGB Instagram 4:5 canvas."""

    return Image.new("RGB", SLIDE_SIZE, background)


def draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    box: tuple[int, int, int, int],
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int],
    spacing: int = 12,
) -> None:
    """Draw simple word-wrapped text inside a bounding box."""

    left, top, right, bottom = box
    max_width = right - left
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        width = draw.textbbox((0, 0), candidate, font=font)[2]
        if current and width > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)

    y = top
    for line in lines:
        bbox = draw.textbbox((left, y), line, font=font)
        line_height = bbox[3] - bbox[1]
        if y + line_height > bottom:
            raise ValueError("Text does not fit in the requested box")
        draw.text((left, y), line, font=font, fill=fill)
        y += line_height + spacing


def save_instagram_jpeg(image: Image.Image, destination: Path | str) -> Path:
    """Save and verify a final 1080×1350 RGB JPEG."""

    destination = Path(destination)
    if image.size != SLIDE_SIZE:
        raise ValueError(f"Expected {SLIDE_SIZE}, got {image.size}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(
        destination,
        "JPEG",
        quality=JPEG_QUALITY,
        subsampling=0,
        optimize=True,
    )
    with Image.open(destination) as check:
        check.load()
        if check.format != "JPEG" or check.size != SLIDE_SIZE or check.mode != "RGB":
            raise ValueError(f"Invalid Instagram JPEG: {destination}")
    return destination


def make_contact_sheet(
    slides: Sequence[Path | str],
    destination: Path | str,
    columns: int = 3,
    thumb_width: int = 324,
    gap: int = 24,
    background: tuple[int, int, int] = (12, 13, 15),
) -> Path:
    """Create a cross-platform contact sheet using Pillow only."""

    if not slides:
        raise ValueError("At least one slide is required")
    opened: list[Image.Image] = []
    try:
        for slide_path in slides:
            slide = Image.open(slide_path).convert("RGB")
            if slide.size != SLIDE_SIZE:
                raise ValueError(f"Unexpected slide size: {slide_path}: {slide.size}")
            thumb_height = round(thumb_width * SLIDE_SIZE[1] / SLIDE_SIZE[0])
            opened.append(slide.resize((thumb_width, thumb_height), Image.Resampling.LANCZOS))

        columns = max(1, min(columns, len(opened)))
        rows = math.ceil(len(opened) / columns)
        thumb_height = opened[0].height
        width = gap + columns * (thumb_width + gap)
        height = gap + rows * (thumb_height + gap)
        sheet = Image.new("RGB", (width, height), background)
        for index, slide in enumerate(opened):
            x = gap + (index % columns) * (thumb_width + gap)
            y = gap + (index // columns) * (thumb_height + gap)
            sheet.paste(slide, (x, y))

        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(destination, "JPEG", quality=94, subsampling=0, optimize=True)
        with Image.open(destination) as check:
            check.load()
            if check.format != "JPEG":
                raise ValueError(f"Invalid contact sheet: {destination}")
        return destination
    finally:
        for slide in opened:
            slide.close()


def render_portability_sample(destination: Path | str) -> Path:
    """Exercise Cyrillic typography and final JPEG export without making content."""

    image = new_slide()
    draw = ImageDraw.Draw(image)
    display = load_font("display", 112, 700)
    body = load_font("body", 50, 500)
    draw_wrapped_text(
        draw,
        "ПРОВЕРКА КИРИЛЛИЦЫ",
        (84, 120, 996, 430),
        display,
        (242, 210, 82),
        spacing=16,
    )
    draw_wrapped_text(
        draw,
        "Бизнес, команда, рост: Ёжик видит ₽ и цифры 1080 × 1350.",
        (84, 520, 996, 930),
        body,
        (242, 242, 238),
        spacing=18,
    )
    draw.rectangle((84, 1080, 996, 1092), fill=(242, 210, 82))
    return save_instagram_jpeg(image, destination)
