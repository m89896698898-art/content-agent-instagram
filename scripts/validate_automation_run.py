#!/usr/bin/env python3
"""Fail-closed validation gates for each automation phase."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

from PIL import Image

try:
    from .automation_utils import load_json, sha256_file, validated_run_dir
    from .generate_ai_scenes import verify_scene
    from .materialize_phase_a import validate_semantics
    from .project_paths import PROJECT_ROOT
    from .schema_validation import validate_instance
except ImportError:  # Direct execution from scripts/.
    from automation_utils import load_json, sha256_file, validated_run_dir
    from generate_ai_scenes import verify_scene
    from materialize_phase_a import validate_semantics
    from project_paths import PROJECT_ROOT
    from schema_validation import validate_instance


FINAL_REQUIRED_FILES = {
    "caption.txt",
    "sources.md",
    "content_brief.md",
    "quality_report.md",
    "editorial_brief.md",
    "hook_report.md",
    "visual_brief.md",
    "research_report.md",
    "contact_sheet.jpg",
    "preview_safe_sheet.jpg",
}
METRIC_COLUMNS = {
    "publication_url",
    "reach",
    "impressions",
    "likes",
    "comments",
    "saves",
    "sends",
    "profile_visits",
    "follows",
    "leads",
}


def validate_phase_a(run_dir: Path, run_id: str, project_root: Path = PROJECT_ROOT) -> dict:
    run_dir = validated_run_dir(run_dir, run_id, project_root)
    if not (run_dir / ".phase_a_complete").is_file():
        raise ValueError("Phase A completion marker is missing")
    state = load_json(run_dir / "phase_a_state.json")
    validate_instance(state, load_json(project_root / "automation" / "phase_a_state.schema.json"))
    validate_semantics(state, run_id, state["source_commit"])
    image_requests = load_json(run_dir / "image_requests.json")
    validate_instance(
        image_requests,
        load_json(project_root / "automation" / "image_requests.schema.json"),
    )
    if state["run_id"] != run_id or state["image_requests"] != image_requests:
        raise ValueError("Phase A state is inconsistent")
    metadata = load_json(run_dir / "run_metadata.json")
    if metadata["run_id"] != run_id or metadata["source_commit"] != state["source_commit"]:
        raise ValueError("Run metadata is inconsistent")
    if sha256_file(project_root / "data" / "posts_history.csv") != metadata[
        "base_posts_history_sha256"
    ]:
        raise ValueError("posts_history.csv changed before final validation")
    return state


def validate_images(run_dir: Path, run_id: str, project_root: Path = PROJECT_ROOT) -> dict:
    state = validate_phase_a(run_dir, run_id, project_root)
    if not (run_dir / ".images_complete").is_file():
        raise ValueError("Image generation completion marker is missing")
    manifest = load_json(run_dir / "image_results.json")
    if (
        manifest.get("schema_version") != "1.0"
        or manifest.get("run_id") != run_id
        or manifest.get("status") != "IMAGES_COMPLETE"
        or manifest.get("model") != "gpt-image-2"
    ):
        raise ValueError("Invalid image result manifest header")
    requests = state["image_requests"]["requests"]
    results = manifest.get("results")
    if not isinstance(results, list) or len(results) != len(requests):
        raise ValueError("Not every required image request has a result")
    by_filename = {item.get("output_filename"): item for item in results}
    if len(by_filename) != len(results):
        raise ValueError("Duplicate image result filename")
    expected_size = tuple(int(value) for value in manifest["requested_size"].split("x"))
    for request in requests:
        result = by_filename.get(request["output_filename"])
        if result is None or result.get("slide_number") != request["slide_number"]:
            raise ValueError(f"Required scene result missing: {request['output_filename']}")
        path = run_dir / "scenes" / request["output_filename"]
        details = verify_scene(path, expected_size)
        if details["sha256"] != result.get("sha256"):
            raise ValueError(f"Scene checksum mismatch: {path.name}")
    return manifest


def _validate_jpeg(path: Path, expected_size: tuple[int, int] | None = None) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"Missing JPG: {path}")
    with Image.open(path) as image:
        image.load()
        if image.format != "JPEG":
            raise ValueError(f"Not a JPEG: {path}")
        if expected_size is not None and image.size != expected_size:
            raise ValueError(f"Unexpected JPG size {image.size}: {path}")
        if expected_size is not None and image.mode != "RGB":
            raise ValueError(f"Final slide must be RGB: {path}")


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"CSV header is missing: {path}")
        return reader.fieldnames, list(reader)


def _validate_staged_history(run_dir: Path, project_root: Path) -> None:
    original_header, original_rows = _read_csv(project_root / "data" / "posts_history.csv")
    staged = run_dir / "staged_data" / "posts_history.csv"
    staged_header, staged_rows = _read_csv(staged)
    if staged_header != original_header:
        raise ValueError("Staged posts_history.csv header changed")
    if len(staged_rows) != len(original_rows) + 1:
        raise ValueError("Staged posts_history.csv must add exactly one row")
    if staged_rows[:-1] != original_rows:
        raise ValueError("Existing posts_history.csv rows were modified")
    new_row = staged_rows[-1]
    if new_row.get("status") != "ready_for_review_not_published":
        raise ValueError("New history row must remain not published")
    nonempty_metrics = [column for column in METRIC_COLUMNS if new_row.get(column, "").strip()]
    if nonempty_metrics:
        raise ValueError(f"Fictitious Instagram metrics are forbidden: {nonempty_metrics}")


def validate_final(run_dir: Path, run_id: str, project_root: Path = PROJECT_ROOT) -> dict:
    validate_images(run_dir, run_id, project_root)
    if (run_dir / ".run_complete").exists():
        raise ValueError("Run was already finalized")
    result_path = run_dir / "phase_b_response.json"
    result = load_json(result_path)
    validate_instance(
        result,
        load_json(project_root / "automation" / "phase_b_result.schema.json"),
    )
    if result["run_id"] != run_id:
        raise ValueError("Phase B run_id mismatch")
    state = load_json(run_dir / "phase_a_state.json")
    if result["output_folder"] != state["output_folder"]:
        raise ValueError("Phase B output folder differs from Phase A")

    staged_root = run_dir / "staged_output"
    publication = staged_root / result["output_folder"]
    if not publication.is_dir():
        raise ValueError("Staged publication directory is missing")
    extra_dirs = [path for path in staged_root.iterdir() if path != publication]
    if extra_dirs:
        raise ValueError("staged_output contains unexpected entries")

    expected_slides = [f"{index:02d}.jpg" for index in range(1, len(state["slides"]) + 1)]
    if result["slide_files"] != expected_slides:
        raise ValueError("Phase B slide list must be contiguous and match Phase A")
    actual_slides = sorted(path.name for path in publication.glob("[0-9][0-9].jpg"))
    if actual_slides != expected_slides:
        raise ValueError("Final JPG set does not match the declared slide list")
    expected_entries = set(expected_slides) | FINAL_REQUIRED_FILES
    actual_entries = {path.name for path in publication.iterdir()}
    if actual_entries != expected_entries or any(path.is_dir() for path in publication.iterdir()):
        unexpected = sorted(actual_entries - expected_entries)
        missing_entries = sorted(expected_entries - actual_entries)
        raise ValueError(
            f"Staged publication file contract mismatch; unexpected={unexpected}, "
            f"missing={missing_entries}"
        )
    for filename in expected_slides:
        _validate_jpeg(publication / filename, (1080, 1350))

    missing = sorted(name for name in FINAL_REQUIRED_FILES if not (publication / name).is_file())
    if missing:
        raise ValueError(f"Final publication files are missing: {', '.join(missing)}")
    for filename in FINAL_REQUIRED_FILES - {"contact_sheet.jpg", "preview_safe_sheet.jpg"}:
        if not (publication / filename).read_text(encoding="utf-8").strip():
            raise ValueError(f"Final text file is empty: {filename}")
    _validate_jpeg(publication / "contact_sheet.jpg")
    _validate_jpeg(publication / "preview_safe_sheet.jpg")
    _validate_staged_history(run_dir, project_root)

    for path in run_dir.rglob("*"):
        if path.is_file() and path.stat().st_size <= 2 * 1024 * 1024:
            if path.suffix.lower() in {".json", ".md", ".txt", ".csv", ".py"}:
                text = path.read_text(encoding="utf-8", errors="ignore")
                if re.search(r"sk-[A-Za-z0-9_-]{20,}", text):
                    raise ValueError(f"Potential API key found in run files: {path}")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("a", "images", "final"), required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.phase == "a":
        validate_phase_a(args.run_dir, args.run_id)
    elif args.phase == "images":
        validate_images(args.run_dir, args.run_id)
    else:
        validate_final(args.run_dir, args.run_id)
    print(f"PASS automation_phase={args.phase}")


if __name__ == "__main__":
    main()
