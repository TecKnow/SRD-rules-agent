"""Build static assets for the exported question-set browser."""

from __future__ import annotations

import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
APP_DIR = ROOT / "apps" / "question-set"
PUBLIC_DIR = APP_DIR / "public"
NOTEBOOK_SRC = ROOT / "ai-test-corpus-explore.py"
NOTEBOOK_DST = APP_DIR / "notebook.py"
TEST_FILES_SRC = ROOT / "Resources" / "Test files"
SRD_MARKDOWN_SRC = ROOT / "data" / "source" / "downfallx-dnd-5e-srd-markdown"

TEST_FILE_NAMES = (
    "benchmark.jsonl",
    "questions_only.jsonl",
    "model_outputs_template.jsonl",
)
EXCLUDED_MARKDOWN_NAMES = frozenset({"README.md", "CHANGELOG.md", "CONTRIBUTING.md"})


def copy_test_files() -> None:
    target = PUBLIC_DIR / "test-files"
    target.mkdir(parents=True, exist_ok=True)
    for name in TEST_FILE_NAMES:
        shutil.copy2(TEST_FILES_SRC / name, target / name)


def copy_srd_markdown() -> None:
    target = PUBLIC_DIR / "srd-markdown"
    target.mkdir(parents=True, exist_ok=True)
    files = []
    for source in sorted(SRD_MARKDOWN_SRC.glob("*.md")):
        if source.name in EXCLUDED_MARKDOWN_NAMES:
            continue
        destination = target / source.name
        shutil.copy2(source, destination)
        files.append({"name": source.name})
    (target / "manifest.json").write_text(
        json.dumps({"files": files}, indent=2) + "\n",
        encoding="utf-8",
    )


def copy_notebook() -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(NOTEBOOK_SRC, NOTEBOOK_DST)


def main() -> None:
    copy_notebook()
    copy_test_files()
    copy_srd_markdown()


if __name__ == "__main__":
    main()
