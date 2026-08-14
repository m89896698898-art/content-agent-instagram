#!/usr/bin/env python3
"""Verify an Actions artifact and copy its payload into a checked-out main branch."""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

try:
    from .automation_utils import (
        atomic_write_bytes,
        load_json,
        require_within,
        sha256_file,
        validated_output_folder,
    )
except ImportError:  # Direct execution from scripts/.
    from automation_utils import (
        atomic_write_bytes,
        load_json,
        require_within,
        sha256_file,
        validated_output_folder,
    )


def persist(artifact: Path, repository: Path) -> Path:
    artifact = artifact.resolve()
    repository = repository.resolve()
    manifest = load_json(artifact / "AUTOMATION_ARTIFACT_MANIFEST.json")
    if manifest.get("schema_version") != "1.0":
        raise ValueError("Unsupported artifact manifest")
    payload = artifact / "repository_payload"
    output_folder = validated_output_folder(manifest["output_folder"])
    expected_paths: set[str] = set()
    for item in manifest.get("files", []):
        relative = item.get("path")
        if not isinstance(relative, str) or relative.startswith("/"):
            raise ValueError("Unsafe artifact path")
        source = require_within(payload / relative, payload, "artifact file")
        if not source.is_file() or sha256_file(source) != item.get("sha256"):
            raise ValueError(f"Artifact checksum mismatch: {relative}")
        if relative != "data/posts_history.csv" and not relative.startswith(
            f"output/{output_folder}/"
        ):
            raise ValueError(f"Artifact contains a disallowed repository path: {relative}")
        if relative in expected_paths:
            raise ValueError(f"Duplicate artifact manifest path: {relative}")
        expected_paths.add(relative)
    actual_paths = {path.relative_to(payload).as_posix() for path in payload.rglob("*") if path.is_file()}
    if actual_paths != expected_paths:
        raise ValueError("Artifact file list does not match its manifest")

    history = repository / "data" / "posts_history.csv"
    if sha256_file(history) != manifest["base_posts_history_sha256"]:
        raise ValueError("main posts_history.csv changed since the run started; refusing overwrite")
    source_output = require_within(payload / "output" / output_folder, payload, "artifact output")
    destination_output = repository / "output" / output_folder
    if destination_output.exists():
        raise FileExistsError(f"Output already exists on main: {destination_output}")
    pending = repository / "output" / f".persist-{manifest['run_id']}-{output_folder}"
    if pending.exists():
        raise FileExistsError(f"Pending persist path exists: {pending}")
    shutil.copytree(source_output, pending)
    try:
        os.replace(pending, destination_output)
        atomic_write_bytes(history, (payload / "data" / "posts_history.csv").read_bytes())
    except BaseException:
        if pending.exists():
            shutil.rmtree(pending)
        raise
    return destination_output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--repository", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    destination = persist(args.artifact, args.repository)
    print(f"PASS persist_payload={destination}")


if __name__ == "__main__":
    main()
