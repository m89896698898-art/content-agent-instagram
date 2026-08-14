#!/usr/bin/env python3
"""Validate Codex Phase A output and atomically materialize run state."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

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


MARKDOWN_FILES = {
    "content_brief_markdown": "content_brief.md",
    "editorial_brief_markdown": "editorial_brief.md",
    "hook_report_markdown": "hook_report.md",
    "visual_brief_markdown": "visual_brief.md",
    "research_report_markdown": "research_report.md",
}


def validate_semantics(state: dict, expected_run_id: str, expected_source_commit: str) -> None:
    if state["run_id"] != expected_run_id:
        raise ValueError("Phase A run_id does not match the GitHub run")
    if state["source_commit"] != expected_source_commit:
        raise ValueError("Phase A source_commit does not match the checked-out commit")
    if not state["output_folder"].startswith(f"{state['publication_date']}_"):
        raise ValueError("output_folder must begin with publication_date")

    slides = state["slides"]
    expected_numbers = list(range(1, len(slides) + 1))
    numbers = [slide["slide_number"] for slide in slides]
    if numbers != expected_numbers:
        raise ValueError("Slide numbers must be contiguous and start at 1")

    hooks = state["hooks"]
    if len(set(hooks["all_15"])) != 15:
        raise ValueError("The 15 hooks must be substantially distinct at least by exact text")
    if not set(hooks["shortlist_5"]).issubset(hooks["all_15"]):
        raise ValueError("shortlist_5 must be selected from all_15")
    if not set(hooks["finalists_3"]).issubset(hooks["shortlist_5"]):
        raise ValueError("finalists_3 must be selected from shortlist_5")
    if hooks["winner"] not in hooks["finalists_3"]:
        raise ValueError("The winning hook must be one of finalists_3")

    requests = state["image_requests"]["requests"]
    filenames = [request["output_filename"] for request in requests]
    request_slides = [request["slide_number"] for request in requests]
    if len(set(filenames)) != len(filenames) or len(set(request_slides)) != len(request_slides):
        raise ValueError("Image request filenames and slide numbers must be unique")

    by_slide = {request["slide_number"]: request["output_filename"] for request in requests}
    for slide in slides:
        declared = slide["ai_scene_output_filename"]
        expected = by_slide.get(slide["slide_number"], "")
        if declared != expected:
            raise ValueError(
                f"Slide {slide['slide_number']} AI filename does not match image_requests"
            )
    if not any(source["source_type"] == "primary" for source in state["sources"]):
        raise ValueError("At least one primary source is required")


def materialize(
    response_path: Path,
    run_dir: Path,
    expected_run_id: str,
    expected_source_commit: str,
    expected_posts_history_sha: str,
    project_root: Path = PROJECT_ROOT,
) -> None:
    run_dir = validated_run_dir(run_dir, expected_run_id, project_root)
    response_path = response_path.resolve()
    if response_path.parent != run_dir:
        raise ValueError("Phase A response must be directly inside the run directory")

    state = load_json(response_path)
    schema = load_json(project_root / "automation" / "phase_a_state.schema.json")
    validate_instance(state, schema)
    validate_semantics(state, expected_run_id, expected_source_commit)

    posts_history = project_root / "data" / "posts_history.csv"
    current_sha = sha256_file(posts_history)
    if current_sha != expected_posts_history_sha:
        raise ValueError("PHASE A must not modify data/posts_history.csv")

    image_schema = load_json(project_root / "automation" / "image_requests.schema.json")
    validate_instance(state["image_requests"], image_schema)

    atomic_write_json(run_dir / "phase_a_state.json", state)
    atomic_write_json(run_dir / "image_requests.json", state["image_requests"])
    for field, filename in MARKDOWN_FILES.items():
        atomic_write_text(run_dir / filename, state[field].rstrip() + "\n")
    atomic_write_text(run_dir / "caption_draft.txt", state["caption"].rstrip() + "\n")
    atomic_write_json(
        run_dir / "run_metadata.json",
        {
            "run_id": expected_run_id,
            "source_commit": expected_source_commit,
            "base_posts_history_sha256": current_sha,
            "materialized_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        },
    )
    atomic_write_text(run_dir / ".phase_a_complete", "PHASE_A_COMPLETE\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--response", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--expected-run-id", required=True)
    parser.add_argument("--expected-source-commit", required=True)
    parser.add_argument("--expected-posts-history-sha", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    materialize(
        args.response,
        args.run_dir,
        args.expected_run_id,
        args.expected_source_commit,
        args.expected_posts_history_sha,
    )
    print("PASS phase_a_state=validated_and_materialized")


if __name__ == "__main__":
    main()
