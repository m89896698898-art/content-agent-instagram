"""Shared, dependency-free helpers for the GitHub Actions automation layer."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

try:
    from .project_paths import PROJECT_ROOT
except ImportError:  # Direct execution from scripts/.
    from project_paths import PROJECT_ROOT


OUTPUT_FOLDER_PATTERN = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}_[a-z0-9]+(?:-[a-z0-9]+)*$"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def atomic_write_bytes(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def atomic_write_text(path: Path, value: str) -> None:
    atomic_write_bytes(path, value.encode("utf-8"))


def atomic_write_json(path: Path, value: Any) -> None:
    rendered = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    atomic_write_text(path, rendered)


def require_within(path: Path, root: Path, label: str) -> Path:
    resolved_path = path.resolve()
    resolved_root = root.resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"{label} must be inside {resolved_root}: {resolved_path}") from exc
    return resolved_path


def validated_run_dir(
    run_dir: Path,
    run_id: str,
    project_root: Path = PROJECT_ROOT,
) -> Path:
    if not re.fullmatch(r"[0-9]+", run_id):
        raise ValueError("run_id must contain digits only")
    state_root = project_root.resolve() / "automation_state"
    resolved = require_within(run_dir, state_root, "run directory")
    if resolved.parent != state_root or resolved.name != run_id:
        raise ValueError(f"run directory must equal automation_state/{run_id}")
    return resolved


def validated_output_folder(name: str) -> str:
    if not OUTPUT_FOLDER_PATTERN.fullmatch(name):
        raise ValueError(f"Invalid output folder name: {name!r}")
    return name
