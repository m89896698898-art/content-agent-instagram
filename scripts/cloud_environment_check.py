#!/usr/bin/env python3
"""Fail-fast Cloud readiness check. Creates no publication artifacts."""

from __future__ import annotations

import hashlib
import sys
import tempfile
from pathlib import Path

import PIL
from PIL import Image

try:
    from .project_paths import OUTPUT_DIR, PROJECT_ROOT, require_project_layout
    from .render_utils import (
        SLIDE_SIZE,
        FONT_FILES,
        font_path,
        load_font,
        make_contact_sheet,
        render_portability_sample,
    )
except ImportError:  # Direct execution from scripts/.
    from project_paths import OUTPUT_DIR, PROJECT_ROOT, require_project_layout
    from render_utils import (
        SLIDE_SIZE,
        FONT_FILES,
        font_path,
        load_font,
        make_contact_sheet,
        render_portability_sample,
    )


EXPECTED_FONT_SHA256 = {
    "display": "5b38c246e255a12f5712d640d56bcced0472466fc68983d2d0410ec0457c2817",
    "body": "1b3a7437ba2af80e465e773ed60c5036d1ba6ace492d89046dbcf18fb31e4e88",
}
EXPECTED_PILLOW_VERSION = "12.3.0"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_font(role: str) -> None:
    path = font_path(role)
    if sha256(path) != EXPECTED_FONT_SHA256[role]:
        raise RuntimeError(f"Unexpected font contents: {path}")
    font = load_font(role, 72, 700 if role == "display" else 500)
    replacement = bytes(font.getmask("�"))
    for char in "АБВГДЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдежзийклмнопрстуфхцчшщъыьэюяЁё₽":
        mask = font.getmask(char)
        if mask.getbbox() is None or bytes(mask) == replacement:
            raise RuntimeError(f"Font {path.name} cannot render {char!r}")


def check_output_writable() -> None:
    handle = tempfile.NamedTemporaryFile(prefix=".cloud-check-", dir=OUTPUT_DIR, delete=False)
    path = Path(handle.name)
    try:
        handle.write(b"ok")
        handle.close()
        if path.read_bytes() != b"ok":
            raise RuntimeError("output/ write/read test failed")
    finally:
        try:
            handle.close()
        finally:
            path.unlink(missing_ok=True)


def main() -> None:
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError(f"Python 3.12 required, found {sys.version.split()[0]}")
    if PIL.__version__ != EXPECTED_PILLOW_VERSION:
        raise RuntimeError(
            f"Pillow {EXPECTED_PILLOW_VERSION} required, found {PIL.__version__}"
        )
    require_project_layout()
    if not PROJECT_ROOT.is_absolute():
        raise RuntimeError("PROJECT_ROOT must resolve to an absolute path")
    for role in FONT_FILES:
        check_font(role)
    check_output_writable()

    with tempfile.TemporaryDirectory(prefix="content-agent-cloud-check-") as temp_dir:
        temp = Path(temp_dir)
        slide = render_portability_sample(temp / "cyrillic-1080x1350.jpg")
        with Image.open(slide) as image:
            image.load()
            if image.format != "JPEG" or image.size != SLIDE_SIZE or image.mode != "RGB":
                raise RuntimeError("JPG validation failed")
        sheet = make_contact_sheet([slide, slide], temp / "contact_sheet.jpg", columns=2)
        with Image.open(sheet) as image:
            image.load()
            if image.format != "JPEG":
                raise RuntimeError("Reusable contact-sheet renderer failed")

    print(f"PASS PROJECT_ROOT={PROJECT_ROOT}")
    print(f"PASS runtime=Python {sys.version.split()[0]}")
    print(f"PASS dependencies=Pillow {PIL.__version__}")
    print("PASS fonts=Oswald-Variable,Rubik-Variable cyrillic=yes")
    print("PASS jpeg=1080x1350 RGB")
    print("PASS output=writable")
    print("PASS reusable_renderer=slide+contact_sheet")
    print("PASS temporary_artifacts=removed")


if __name__ == "__main__":
    main()
