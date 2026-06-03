from __future__ import annotations

import argparse
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .io import DEFAULT_BENCHMARK_PATH, DEFAULT_RUNS_DIR, compact_metadata, read_jsonl, require_new_file, write_jsonl
from .openrouter import OpenRouterClient


PROMPT_VERSION = "no-rag-baseline-v1"

SYSTEM_PROMPT = """You answer questions about D&D SRD 5.2.1 rules.

This is a no-RAG baseline: you are not receiving retrieved source passages.
Answer from your own knowledge, but keep the response scoped to SRD 5.2.1.
Do not import Pathfinder, D&D 2014, forum rulings, or non-SRD 2024 material.
If the SRD answer is uncertain or ambiguous, say so plainly.
Do not invent citations. If you cannot cite an exact source, answer without citations."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gather no-RAG model answers for the SRD benchmark.")
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK_PATH)
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--model", action="append", dest="models", help="OpenRouter model id. Repeat for multiple models.")
    parser.add_argument("--limit", type=int, default=None, help="Optional smoke-test row limit.")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=1600)
    parser.add_argument("--timeout-seconds", type=int, default=120)
    return parser.parse_args()


def models_from_args(values: list[str] | None) -> list[str]:
    if values:
        return values
    env_value = os.environ.get("OPENROUTER_MODELS", "")
    models = [item.strip() for item in env_value.split(",") if item.strip()]
    if models:
        return models
    raise RuntimeError("Provide at least one --model or set OPENROUTER_MODELS as a comma-separated list")


def make_user_prompt(row: dict[str, Any]) -> str:
    metadata = compact_metadata(row)
    metadata_lines = "\n".join(f"- {key}: {value}" for key, value in metadata.items())
    return f"""Question:
{row["question"]}

Benchmark metadata, for scoping only:
{metadata_lines}

Give the best no-RAG answer you can."""


def output_path(args: argparse.Namespace, run_id: str) -> Path:
    if args.output:
        return args.output
    return args.runs_dir / run_id / "answers.jsonl"


def build_records(args: argparse.Namespace) -> tuple[Path, list[dict[str, Any]]]:
    run_id = args.run_id or f"no-rag-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    path = output_path(args, run_id)
    require_new_file(path)

    client = OpenRouterClient(timeout_seconds=args.timeout_seconds)
    models = models_from_args(args.models)
    benchmark_rows = list(read_jsonl(args.benchmark))
    if args.limit is not None:
        benchmark_rows = benchmark_rows[: args.limit]

    records: list[dict[str, Any]] = []
    for row in benchmark_rows:
        for model in models:
            result = client.chat(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": make_user_prompt(row)},
                ],
                temperature=args.temperature,
                max_tokens=args.max_tokens,
            )
            records.append(
                {
                    "run_id": run_id,
                    "pipeline": "no_rag",
                    "question_id": row["id"],
                    "model": model,
                    "prompt_version": PROMPT_VERSION,
                    "question": row["question"],
                    "answer": result.text,
                    "benchmark_metadata": compact_metadata(row),
                    "raw_response": result.raw_response,
                    "generated_at": datetime.now(UTC).isoformat(),
                }
            )
    return path, records


def main() -> None:
    args = parse_args()
    path, records = build_records(args)
    count = write_jsonl(path, records)
    print(f"Wrote {count} no-RAG answer records to {path}")


if __name__ == "__main__":
    main()
