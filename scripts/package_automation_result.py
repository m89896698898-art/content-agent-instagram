#!/usr/bin/env python3
"""Build a secret-free artifact containing only the completed publication payload."""

from __future__ import annotations

import argparse
import os
import shutil
import tempfile
from pathlib import Path

try:
    from .automation_utils import (
        atomic_write_json,
        load_json,
        sha256_file,
        validated_run_dir,
    )
    from .project_paths import PROJECT_ROOT
except ImportError:  # Direct execution from scripts/.
    from automation_utils import atomic_write_json, load_json, sha256_file, validated_run_dir
    from project_paths import PROJECT_ROOT


def package_result(
    run_dir: Path,
    run_id: str,
    project_root: Path = PROJECT_ROOT,
) -> Path:
    run_dir = validated_run_dir(run_dir, run_id, project_root)
    if not (run_dir / ".run_complete").is_file():
        raise ValueError("Only a completed run can be packaged")
    state = load_json(run_dir / "phase_a_state.json")
    metadata = load_json(run_dir / "run_metadata.json")
    output_folder = state["output_folder"]
    publication = project_root / "output" / output_folder
    if not publication.is_dir():
        raise FileNotFoundError(publication)

    artifact = run_dir / "artifact"
    if artifact.exists():
        raise FileExistsError(f"Artifact already exists: {artifact}")
    with tempfile.TemporaryDirectory(prefix=".artifact-", dir=run_dir) as temporary_name:
        temporary = Path(temporary_name)
        payload = temporary / "repository_payload"
        shutil.copytree(publication, payload / "output" / output_folder)
        (payload / "data").mkdir(parents=True)
        shutil.copy2(project_root / "data" / "posts_history.csv", payload / "data")

        files = []
        for path in sorted(payload.rglob("*")):
            if path.is_file():
                files.append(
                    {
                        "path": path.relative_to(payload).as_posix(),
                        "bytes": path.stat().st_size,
                        "sha256": sha256_file(path),
                    }
                )
        manifest = {
            "schema_version": "1.0",
            "run_id": run_id,
            "source_commit": metadata["source_commit"],
            "base_posts_history_sha256": metadata["base_posts_history_sha256"],
            "output_folder": output_folder,
            "files": files,
        }
        atomic_write_json(temporary / "AUTOMATION_ARTIFACT_MANIFEST.json", manifest)
        shutil.copy2(run_dir / "phase_a_state.json", temporary / "phase_a_state.json")
        shutil.copy2(run_dir / "image_results.json", temporary / "image_results.json")
        shutil.copy2(run_dir / "phase_b_response.json", temporary / "phase_b_response.json")
        os.replace(temporary, artifact)
    return artifact


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    artifact = package_result(args.run_dir, args.run_id)
    print(f"PASS artifact={artifact}")


if __name__ == "__main__":
    main()
