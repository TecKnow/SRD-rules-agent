import json
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any


type JsonObject = dict[str, Any]

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BENCHMARK_PATH = ROOT / "Resources" / "Test files" / "benchmark.jsonl"
DEFAULT_RUNS_DIR = ROOT / "runs" / "no_rag"


def read_jsonl(path: Path) -> Iterator[JsonObject]:
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                value = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number} is not valid JSONL") from exc
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number} must contain a JSON object")
            yield value


def write_jsonl(path: Path, rows: Iterable[JsonObject]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            handle.write("\n")
            count += 1
    return count


def require_new_file(path: Path) -> None:
    if path.exists():
        raise FileExistsError(f"{path} already exists; choose a new run id or output path")


def compact_metadata(row: JsonObject) -> JsonObject:
    keys = [
        "category",
        "difficulty",
        "answer_status",
        "contentiousness",
        "curation_status",
        "verification_status",
        "version_specificity",
        "gold_dataset_linked",
        "gold_link_status",
        "linked_gold_ids",
        "tags",
        "topic",
    ]
    return {key: row.get(key) for key in keys if key in row}
