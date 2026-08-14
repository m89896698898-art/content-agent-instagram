#!/usr/bin/env python3
"""Restricted OpenAI Image API adapter for CONTENT AGENT AI scene generation."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable

from PIL import Image

try:
    from .automation_utils import (
        atomic_write_json,
        atomic_write_text,
        load_json,
        sha256_file,
        validated_run_dir,
    )
    from .project_paths import PROJECT_ROOT
    from .schema_validation import validate_instance
except ImportError:  # Direct execution from scripts/.
    from automation_utils import (
        atomic_write_json,
        atomic_write_text,
        load_json,
        sha256_file,
        validated_run_dir,
    )
    from project_paths import PROJECT_ROOT
    from schema_validation import validate_instance


API_URL = "https://api.openai.com/v1/images/generations"
MODEL = "gpt-image-2"
DEFAULT_QUALITY = "medium"
DEFAULT_SIZE = "1024x1280"
HARD_MAX_IMAGES = 4
MAX_RESPONSE_BYTES = 40 * 1024 * 1024
ABSENCE_SUFFIX = (
    " Create only a clean background scene for later graphic design. "
    "No text, no letters, no words, no numbers, no logos, no trademarks, "
    "no interface labels, no signatures, and no watermarks anywhere in the image."
)


class ImageGenerationError(RuntimeError):
    """A safe, non-secret-bearing Image API failure."""


def validate_size(value: str) -> tuple[int, int]:
    try:
        width_text, height_text = value.lower().split("x", 1)
        width, height = int(width_text), int(height_text)
    except (ValueError, AttributeError) as exc:
        raise ValueError("size must use WIDTHxHEIGHT") from exc
    if width % 16 or height % 16:
        raise ValueError("Both image edges must be multiples of 16")
    if max(width, height) > 3840:
        raise ValueError("Maximum image edge is 3840 pixels")
    pixels = width * height
    if not 655_360 <= pixels <= 8_294_400:
        raise ValueError("Image pixel count is outside GPT Image 2 limits")
    if max(width, height) / min(width, height) > 3:
        raise ValueError("Image aspect ratio must not exceed 3:1")
    return width, height


def _safe_api_error(raw: bytes, status: int) -> ImageGenerationError:
    message = f"OpenAI Image API returned HTTP {status}"
    try:
        parsed = json.loads(raw.decode("utf-8"))
        detail = parsed.get("error", {}).get("message")
        if isinstance(detail, str) and detail.strip():
            message = f"{message}: {detail.strip()[:500]}"
    except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
        pass
    return ImageGenerationError(message)


def request_image(api_key: str, payload: dict) -> bytes:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "content-agent-github-actions/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise ImageGenerationError("OpenAI Image API response exceeded safety limit")
    except urllib.error.HTTPError as exc:
        raw_error = exc.read(64 * 1024)
        raise _safe_api_error(raw_error, exc.code) from exc
    except urllib.error.URLError as exc:
        raise ImageGenerationError(f"OpenAI Image API network failure: {exc.reason}") from exc

    try:
        response_json = json.loads(raw.decode("utf-8"))
        encoded = response_json["data"][0]["b64_json"]
        if not isinstance(encoded, str) or not encoded:
            raise KeyError("empty b64_json")
        return base64.b64decode(encoded, validate=True)
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, IndexError, TypeError, ValueError) as exc:
        raise ImageGenerationError("OpenAI Image API response did not contain a valid image") from exc


def verify_scene(path: Path, expected_size: tuple[int, int]) -> dict[str, object]:
    if not path.is_file() or path.stat().st_size == 0:
        raise ImageGenerationError(f"Required scene is missing: {path.name}")
    try:
        with Image.open(path) as image:
            image.load()
            if image.format != "PNG":
                raise ImageGenerationError(f"Scene {path.name} is not PNG")
            if image.size != expected_size:
                raise ImageGenerationError(
                    f"Scene {path.name} has size {image.size}, expected {expected_size}"
                )
            width, height = image.size
            mode = image.mode
    except (OSError, ValueError) as exc:
        raise ImageGenerationError(f"Pillow cannot open scene {path.name}") from exc
    return {
        "filename": path.name,
        "width": width,
        "height": height,
        "format": "PNG",
        "mode": mode,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def _prompt_sha(request: dict) -> str:
    prompt = request["prompt"].rstrip() + ABSENCE_SUFFIX
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def _can_reuse(
    request: dict,
    scene_path: Path,
    previous: dict | None,
    quality: str,
    size: str,
    expected_size: tuple[int, int],
) -> dict[str, object] | None:
    if not previous or not scene_path.is_file():
        return None
    if (
        previous.get("prompt_sha256") != _prompt_sha(request)
        or previous.get("model") != MODEL
        or previous.get("quality") != quality
        or previous.get("requested_size") != size
    ):
        return None
    details = verify_scene(scene_path, expected_size)
    if details["sha256"] != previous.get("sha256"):
        return None
    return details


def generate_scenes(
    run_dir: Path,
    run_id: str,
    api_key: str,
    quality: str = DEFAULT_QUALITY,
    size: str = DEFAULT_SIZE,
    max_images: int = HARD_MAX_IMAGES,
    transport: Callable[[str, dict], bytes] = request_image,
    project_root: Path = PROJECT_ROOT,
) -> dict:
    if not api_key:
        raise ImageGenerationError("OPENAI_API_KEY secret is required")
    if quality not in {"low", "medium", "high"}:
        raise ValueError("quality must be low, medium, or high")
    if not 0 <= max_images <= HARD_MAX_IMAGES:
        raise ValueError(f"max_images must be between 0 and {HARD_MAX_IMAGES}")

    expected_size = validate_size(size)
    run_dir = validated_run_dir(run_dir, run_id, project_root)
    if not (run_dir / ".phase_a_complete").is_file():
        raise ImageGenerationError("Phase A completion marker is missing")

    requests_manifest = load_json(run_dir / "image_requests.json")
    schema = load_json(project_root / "automation" / "image_requests.schema.json")
    validate_instance(requests_manifest, schema)
    requests = requests_manifest["requests"]
    if len(requests) > max_images:
        raise ImageGenerationError(
            f"Image request count {len(requests)} exceeds configured maximum {max_images}"
        )

    results_path = run_dir / "image_results.json"
    previous_results: dict[str, dict] = {}
    if results_path.is_file():
        try:
            previous_manifest = load_json(results_path)
            previous_results = {
                item["output_filename"]: item
                for item in previous_manifest.get("results", [])
                if isinstance(item, dict) and isinstance(item.get("output_filename"), str)
            }
        except (OSError, json.JSONDecodeError, TypeError):
            previous_results = {}

    scenes_dir = run_dir / "scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / ".images_complete").unlink(missing_ok=True)
    generated = 0
    reused = 0
    result_items: list[dict] = []

    for item in requests:
        filename = item["output_filename"]
        if Path(filename).name != filename:
            raise ImageGenerationError(f"Unsafe scene filename: {filename!r}")
        scene_path = scenes_dir / filename
        details = _can_reuse(
            item,
            scene_path,
            previous_results.get(filename),
            quality,
            size,
            expected_size,
        )
        if details is None:
            prompt = item["prompt"].rstrip() + ABSENCE_SUFFIX
            payload = {
                "model": MODEL,
                "prompt": prompt,
                "n": 1,
                "size": size,
                "quality": quality,
                "output_format": "png",
            }
            image_bytes = transport(api_key, payload)
            with tempfile.TemporaryDirectory(prefix=".image-api-", dir=run_dir) as temporary:
                temporary_path = Path(temporary) / filename
                temporary_path.write_bytes(image_bytes)
                details = verify_scene(temporary_path, expected_size)
                os.replace(temporary_path, scene_path)
            details = verify_scene(scene_path, expected_size)
            generated += 1
        else:
            reused += 1

        result_items.append(
            {
                "slide_number": item["slide_number"],
                "output_filename": filename,
                "model": MODEL,
                "quality": quality,
                "requested_size": size,
                "prompt_sha256": _prompt_sha(item),
                **details,
            }
        )

    for item in result_items:
        verify_scene(scenes_dir / item["output_filename"], expected_size)

    result = {
        "schema_version": "1.0",
        "run_id": run_id,
        "status": "IMAGES_COMPLETE",
        "model": MODEL,
        "quality": quality,
        "requested_size": size,
        "requested_count": len(requests),
        "api_calls": generated,
        "reused_count": reused,
        "results": result_items,
    }
    atomic_write_json(results_path, result)
    atomic_write_text(run_dir / ".images_complete", "IMAGES_COMPLETE\n")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--quality", default=DEFAULT_QUALITY, choices=("low", "medium", "high"))
    parser.add_argument("--size", default=DEFAULT_SIZE)
    parser.add_argument("--max-images", type=int, default=HARD_MAX_IMAGES)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    api_key = os.environ.get("OPENAI_API_KEY", "")
    result = generate_scenes(
        args.run_dir,
        args.run_id,
        api_key,
        args.quality,
        args.size,
        args.max_images,
    )
    print(f"PASS image_generation_calls={result['api_calls']}")
    print(f"PASS reused_scenes={result['reused_count']}")
    print(f"PASS required_scenes={result['requested_count']}")


if __name__ == "__main__":
    main()
