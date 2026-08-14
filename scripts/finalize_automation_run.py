#!/usr/bin/env python3
"""Promote a fully validated staged run into the ephemeral checkout atomically."""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

try:
    from .automation_utils import (
        atomic_write_bytes,
        atomic_write_text,
        load_json,
        sha256_file,
        validated_run_dir,
    )
    from .project_paths import PROJECT_ROOT
    from .validate_automation_run import validate_final
except ImportError:  # Direct execution from scripts/.
    from automation_utils import (
        atomic_write_bytes,
        atomic_write_text,
        load_json,
        sha256_file,
        validated_run_dir,
    )
    from project_paths import PROJECT_ROOT
    from validate_automation_run import validate_final


def finalize(
    run_dir: Path,
    run_id: str,
    project_root: Path = PROJECT_ROOT,
) -> Path:
    run_dir = validated_run_dir(run_dir, run_id, project_root)
    result = validate_final(run_dir, run_id, project_root)
    metadata = load_json(run_dir / "run_metadata.json")
    history_path = project_root / "data" / "posts_history.csv"
    if sha256_file(history_path) != metadata["base_posts_history_sha256"]:
        raise ValueError("posts_history.csv changed during the run")

    output_folder = result["output_folder"]
    staged_publication = run_dir / "staged_output" / output_folder
    final_publication = project_root / "output" / output_folder
    if final_publication.exists():
        raise FileExistsError(f"Output already exists: {final_publication}")

    pending = project_root / "output" / f".automation-{run_id}-{output_folder}"
    if pending.exists():
        raise FileExistsError(f"Pending output already exists: {pending}")
    shutil.copytree(staged_publication, pending)
    try:
        os.replace(pending, final_publication)
        staged_history = run_dir / "staged_data" / "posts_history.csv"
        atomic_write_bytes(history_path, staged_history.read_bytes())
    except BaseException:
        if pending.exists():
            shutil.rmtree(pending)
        raise

    atomic_write_text(run_dir / ".run_complete", "RUN_COMPLETE\n")
    return final_publication


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = finalize(args.run_dir, args.run_id)
    print(f"PASS finalized_output={result.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
