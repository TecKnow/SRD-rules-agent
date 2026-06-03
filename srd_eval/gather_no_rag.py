import argparse
import os
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

from .config import load_env
from .io import (
    DEFAULT_BENCHMARK_PATH,
    DEFAULT_RUNS_DIR,
    JsonObject,
    append_jsonl,
    compact_metadata,
    read_jsonl,
    require_new_file,
)
from .openrouter import OpenRouterClient


PROMPT_VERSION = "no-rag-baseline-v1"

SYSTEM_PROMPT = """You answer questions about D&D SRD 5.2.1 rules.

Answer from your own knowledge, but keep the response scoped to SRD 5.2.1.
Do not import Pathfinder, D&D 2014, forum rulings, or non-SRD 2024 material.
When SRD 5.2.1 may differ from older 2014 D&D rules, prefer SRD 5.2.1 and say when you are uncertain.
If the SRD answer is uncertain or ambiguous, say so plainly.
Do not cite page numbers, book sections, or quoted rules text unless those details were provided in the question.
If you are relying on memory, explain the rule without citations."""


def parse_args() -> argparse.Namespace:
    load_env()
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
    parser.add_argument("--resume", action="store_true", help="Append to an existing output and skip completed answers.")
    parser.add_argument("--retries", type=int, default=2, help="Retries for transient request failures.")
    parser.add_argument("--retry-delay-seconds", type=float, default=5.0)
    parser.add_argument("--continue-on-error", action="store_true", help="Record failed requests and keep going.")
    return parser.parse_args()


def models_from_args(values: list[str] | None) -> list[str]:
    if values:
        return values
    env_value = os.environ.get("OPENROUTER_MODELS", "")
    models = [item.strip() for item in env_value.split(",") if item.strip()]
    if models:
        return models
    raise RuntimeError("Provide at least one --model or set OPENROUTER_MODELS as a comma-separated list")


def make_user_prompt(row: JsonObject) -> str:
    return f"""Question:
{row["question"]}"""


def output_path(args: argparse.Namespace, run_id: str) -> Path:
    if args.output:
        return args.output
    return args.runs_dir / run_id / "answers.jsonl"


def new_run_id() -> str:
    return f"no-rag-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"


def existing_run_id(path: Path) -> str | None:
    if not path.exists():
        return None
    for row in read_jsonl(path):
        run_id = row.get("run_id")
        if isinstance(run_id, str) and run_id:
            return run_id
    return None


def completed_pairs(path: Path) -> set[tuple[str, str]]:
    if not path.exists():
        return set()
    return {
        (str(row.get("question_id")), str(row.get("model")))
        for row in read_jsonl(path)
        if row.get("answer") and not row.get("error")
    }


def make_answer_record(run_id: str, row: JsonObject, model: str, result: JsonObject) -> JsonObject:
    return {
        "run_id": run_id,
        "pipeline": "no_rag",
        "question_id": row["id"],
        "model": model,
        "prompt_version": PROMPT_VERSION,
        "question": row["question"],
        "answer": result["text"],
        "benchmark_metadata": compact_metadata(row),
        "raw_response": result["raw_response"],
        "generated_at": datetime.now(UTC).isoformat(),
    }


def make_error_record(run_id: str, row: JsonObject, model: str, error: Exception) -> JsonObject:
    return {
        "run_id": run_id,
        "pipeline": "no_rag",
        "question_id": row["id"],
        "model": model,
        "prompt_version": PROMPT_VERSION,
        "question": row["question"],
        "answer": "",
        "benchmark_metadata": compact_metadata(row),
        "raw_response": {},
        "error": str(error),
        "generated_at": datetime.now(UTC).isoformat(),
    }


def chat_with_retries(
    client: OpenRouterClient,
    *,
    row: JsonObject,
    model: str,
    args: argparse.Namespace,
) -> JsonObject:
    attempts = args.retries + 1
    for attempt in range(1, attempts + 1):
        try:
            result = client.chat(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": make_user_prompt(row)},
                ],
                temperature=args.temperature,
                max_tokens=args.max_tokens,
            )
            return {"text": result.text, "raw_response": result.raw_response}
        except Exception:
            if attempt >= attempts:
                raise
            print(
                f"Retrying {row['id']} with {model} after failure "
                f"({attempt}/{args.retries})...",
                flush=True,
            )
            time.sleep(args.retry_delay_seconds)
    raise AssertionError("unreachable retry loop exit")


def resolve_run(args: argparse.Namespace) -> tuple[str, Path]:
    if args.resume and not args.run_id and not args.output:
        raise RuntimeError("--resume requires --run-id or --output")
    provisional_run_id = args.run_id or new_run_id()
    path = output_path(args, provisional_run_id)
    if args.resume:
        return args.run_id or existing_run_id(path) or provisional_run_id, path
    require_new_file(path)
    return provisional_run_id, path


def gather_records(args: argparse.Namespace) -> tuple[Path, int]:
    run_id, path = resolve_run(args)

    client = OpenRouterClient(timeout_seconds=args.timeout_seconds)
    models = models_from_args(args.models)
    benchmark_rows = list(read_jsonl(args.benchmark))
    if args.limit is not None:
        benchmark_rows = benchmark_rows[: args.limit]

    complete = completed_pairs(path) if args.resume else set()
    planned_pairs = [(row, model) for row in benchmark_rows for model in models]
    total = len(planned_pairs)
    written = 0
    skipped = 0

    print(f"Writing answers to {path}", flush=True)
    print(f"Run id: {run_id}", flush=True)
    print(f"Planned requests: {total} ({len(benchmark_rows)} questions x {len(models)} models)", flush=True)

    for index, (row, model) in enumerate(planned_pairs, start=1):
        pair = (str(row["id"]), model)
        if pair in complete:
            skipped += 1
            print(f"[{index}/{total}] SKIP {row['id']} | {model}", flush=True)
            continue

        print(f"[{index}/{total}] START {row['id']} | {model}", flush=True)
        try:
            result = chat_with_retries(client, row=row, model=model, args=args)
            record = make_answer_record(run_id, row, model, result)
            append_jsonl(path, record)
            written += 1
            print(f"[{index}/{total}] DONE  {row['id']} | {model}", flush=True)
        except Exception as exc:
            append_jsonl(path, make_error_record(run_id, row, model, exc))
            written += 1
            print(f"[{index}/{total}] ERROR {row['id']} | {model}: {exc}", flush=True)
            if not args.continue_on_error:
                print("Stopping after error. Re-run with --resume to continue after fixing the issue.", flush=True)
                raise SystemExit(1)

    print(f"Finished. Appended {written} record(s), skipped {skipped} completed request(s).", flush=True)
    return path, written


def main() -> None:
    args = parse_args()
    path, count = gather_records(args)
    print(f"Wrote {count} no-RAG answer records to {path}")


if __name__ == "__main__":
    main()
