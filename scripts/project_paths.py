"""Portable project paths shared by technical rendering scripts."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"
SKILLS_DIR = PROJECT_ROOT / "skills"
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
ASSETS_DIR = PROJECT_ROOT / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"


def require_project_layout() -> None:
    """Fail clearly when a script is run from an incomplete checkout."""

    required = (
        PROJECT_ROOT / "AGENTS.md",
        KNOWLEDGE_DIR,
        SKILLS_DIR,
        DATA_DIR / "posts_history.csv",
        DATA_DIR / "content_hypotheses.csv",
        OUTPUT_DIR,
        FONTS_DIR,
    )
    missing = [path for path in required if not path.exists()]
    if missing:
        rendered = "\n".join(f"- {path}" for path in missing)
        raise FileNotFoundError(f"Incomplete CONTENT AGENT checkout:\n{rendered}")
