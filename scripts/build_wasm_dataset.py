"""Pre-bake a compact, deduplicated dataset for the WASM RAG-comparison notebook.

The interactive marimo notebook cannot read the run directories from a browser
filesystem, and the raw RAG answers inline the full text of every retrieved
chunk (~8x duplicated across the 900 question/model pairs). This script reuses
the canonical merge/pairing logic from ``build_rag_comparison_report`` so the
summary stats match the published report exactly, then:

  * enriches each pair with the per-side failure-type/notes dicts and the
    retrieved-context *references* (chunk_id + rank + distance) the detail UI
    needs, and
  * dedups chunk bodies into a single ``chunks`` lookup keyed by ``chunk_id``,
    dropping heavy metadata fields the UI never shows.

Output is one JSON file the WASM notebook fetches via ``mo.notebook_location()``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from srd_eval.grade_deepeval import EVALUATOR_VERSION, FAILURE_TYPES
from srd_eval.io import DEFAULT_BENCHMARK_PATH, ROOT, JsonObject, read_jsonl

from build_rag_comparison_report import (
    NO_RAG_ANSWERS_PATH,
    NO_RAG_SCORES_PATH,
    RAG_ANSWERS_PATH,
    RAG_SCORES_PATH,
    build_pair_records,
    merge_score_records,
    pair_key,
    sorted_retrieved_contexts,
)

DEFAULT_OUTPUT = ROOT / "apps" / "rag-comparison" / "public" / "comparison_data.json"

# Extra benchmark dimensions to expose as notebook filters. These live in the
# benchmark but are dropped from the answer records' compact_metadata, so they
# are joined back in here on question_id.
BENCHMARK_FILTER_FIELDS = (
    "source_model",
    "contentiousness",
    "version_specificity",
)

# Chunk metadata fields the notebook context viewer actually surfaces. Everything
# else (content_sha256, source_path, chunk_index, chunking_strategy, ...) is
# dropped to keep the bundle small.
KEEP_CHUNK_METADATA = (
    "source_file",
    "name",
    "entity_type",
    "h1",
    "h2",
    "h3",
    "h4",
    "srd_version",
)

# Decimal places for retrieval distances; 4 is well past what the UI shows.
DISTANCE_DIGITS = 4


def round_distance(value: Any) -> float | None:
    if value is None:
        return None
    return round(float(value), DISTANCE_DIGITS)


def failure_flags(record: JsonObject) -> dict[str, bool]:
    raw = record.get("failure_types", {})
    raw = raw if isinstance(raw, dict) else {}
    return {failure_type: bool(raw.get(failure_type)) for failure_type in FAILURE_TYPES}


def failure_notes(record: JsonObject, flags: dict[str, bool]) -> dict[str, str]:
    raw = record.get("failure_notes", {})
    raw = raw if isinstance(raw, dict) else {}
    # Only carry notes for failures that actually fired; the rest are blank.
    return {
        failure_type: str(raw.get(failure_type, "")).strip()
        for failure_type in FAILURE_TYPES
        if flags[failure_type] and str(raw.get(failure_type, "")).strip()
    }


def trim_chunk_metadata(metadata: Any) -> dict[str, Any]:
    metadata = metadata if isinstance(metadata, dict) else {}
    return {key: metadata[key] for key in KEEP_CHUNK_METADATA if key in metadata}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-rag-scores", type=Path, default=NO_RAG_SCORES_PATH)
    parser.add_argument("--no-rag-answers", type=Path, default=NO_RAG_ANSWERS_PATH)
    parser.add_argument("--rag-scores", type=Path, default=RAG_SCORES_PATH)
    parser.add_argument("--rag-answers", type=Path, default=RAG_ANSWERS_PATH)
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--indent",
        type=int,
        default=None,
        help="Pretty-print with this indent (debugging); default writes compact JSON.",
    )
    return parser.parse_args()


def build_dataset(args: argparse.Namespace) -> dict[str, Any]:
    no_rag_scores = list(read_jsonl(args.no_rag_scores))
    no_rag_answers = list(read_jsonl(args.no_rag_answers))
    rag_scores = list(read_jsonl(args.rag_scores))
    rag_answers = list(read_jsonl(args.rag_answers))
    benchmark_by_id = {str(row["id"]): row for row in read_jsonl(args.benchmark)}

    no_rag_records, no_rag_error_rows = merge_score_records(
        score_records=no_rag_scores,
        answer_records=no_rag_answers,
        answer_set="no_rag",
    )
    rag_records, rag_error_rows = merge_score_records(
        score_records=rag_scores,
        answer_records=rag_answers,
        answer_set="rag",
    )
    pair_records, no_rag_only_count, rag_only_count = build_pair_records(no_rag_records, rag_records)
    if not pair_records:
        raise ValueError("No matched no-RAG/RAG pairs were found; nothing to bake.")

    # Index the merged records (which carry the raw score-row fields, including
    # failure_types/failure_notes via `**score_row`) and the raw RAG answer rows
    # (the only place the full retrieved-context list survives the report merge).
    no_rag_merged_by_key = {pair_key(row): row for row in no_rag_records}
    rag_merged_by_key = {pair_key(row): row for row in rag_records}
    rag_answers_by_key = {pair_key(row): row for row in rag_answers}

    chunks: dict[str, dict[str, Any]] = {}

    def context_refs(answer_row: JsonObject) -> list[dict[str, Any]]:
        refs = []
        for context in sorted_retrieved_contexts(answer_row):
            chunk_id = str(context.get("chunk_id", ""))
            if not chunk_id:
                continue
            if chunk_id not in chunks:
                chunks[chunk_id] = {
                    "text": str(context.get("text", "")),
                    "metadata": trim_chunk_metadata(context.get("metadata", {})),
                }
            refs.append(
                {
                    "chunk_id": chunk_id,
                    "rank": context.get("rank"),
                    "distance": round_distance(context.get("distance")),
                }
            )
        return refs

    pairs = []
    for pair in pair_records:
        key = (pair["question_id"], pair["model"])
        no_rag_merged = no_rag_merged_by_key.get(key, {})
        rag_merged = rag_merged_by_key.get(key, {})
        # Each side's active failure set is derivable in the notebook from the
        # new/resolved/shared lists already on the pair (no_rag = resolved|shared,
        # rag = new|shared), so the full boolean dicts are not emitted. The flags
        # are still computed locally to decide which notes are worth carrying.
        no_rag_flags = failure_flags(no_rag_merged)
        rag_flags = failure_flags(rag_merged)
        benchmark_row = benchmark_by_id.get(pair["question_id"], {})
        enriched = {
            **pair,
            **{field: benchmark_row.get(field, "") for field in BENCHMARK_FILTER_FIELDS},
            "top_distance": round_distance(pair.get("top_distance")),
            "avg_distance": round_distance(pair.get("avg_distance")),
            "no_rag_failure_notes": failure_notes(no_rag_merged, no_rag_flags),
            "rag_failure_notes": failure_notes(rag_merged, rag_flags),
            "no_rag_diagnostic_confidence": no_rag_merged.get("diagnostic_confidence", ""),
            "rag_diagnostic_confidence": rag_merged.get("diagnostic_confidence", ""),
            "retrieved_context": context_refs(rag_answers_by_key.get(key, {})),
        }
        pairs.append(enriched)

    paired_count = len(pairs)
    improved = sum(1 for row in pairs if row["score_delta"] > 0)
    declined = sum(1 for row in pairs if row["score_delta"] < 0)
    summary = {
        "paired_count": paired_count,
        "no_rag_records": len(no_rag_records),
        "rag_records": len(rag_records),
        "improved": improved,
        "declined": declined,
        "unchanged": paired_count - improved - declined,
        "no_rag_pass_count": sum(1 for row in pairs if row["no_rag_passed"]),
        "rag_pass_count": sum(1 for row in pairs if row["rag_passed"]),
        "average_no_rag_score": round(sum(row["no_rag_score"] for row in pairs) / paired_count, 4),
        "average_rag_score": round(sum(row["rag_score"] for row in pairs) / paired_count, 4),
        "average_score_delta": round(sum(row["score_delta"] for row in pairs) / paired_count, 4),
        # Not derivable from the matched pairs alone, so carried explicitly.
        "no_rag_only_count": no_rag_only_count,
        "rag_only_count": rag_only_count,
        "no_rag_score_errors": len(no_rag_error_rows),
        "rag_score_errors": len(rag_error_rows),
    }

    return {
        "meta": {
            "evaluator_version": EVALUATOR_VERSION,
            "failure_types": list(FAILURE_TYPES),
            "sources": {
                "no_rag_scores": args.no_rag_scores.relative_to(ROOT).as_posix(),
                "no_rag_answers": args.no_rag_answers.relative_to(ROOT).as_posix(),
                "rag_scores": args.rag_scores.relative_to(ROOT).as_posix(),
                "rag_answers": args.rag_answers.relative_to(ROOT).as_posix(),
                "benchmark": args.benchmark.relative_to(ROOT).as_posix(),
            },
            "benchmark_filter_fields": list(BENCHMARK_FILTER_FIELDS),
            "unique_chunks": len(chunks),
        },
        "summary": summary,
        "pairs": pairs,
        "chunks": chunks,
    }


def main() -> None:
    args = parse_args()
    dataset = build_dataset(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(
            dataset,
            handle,
            ensure_ascii=False,
            sort_keys=True,
            indent=args.indent,
            separators=None if args.indent else (",", ":"),
        )
        handle.write("\n")

    size_kb = args.output.stat().st_size / 1024
    summary = dataset["summary"]
    print(f"Wrote {args.output.relative_to(ROOT).as_posix()} ({size_kb:.0f} KB)")
    print(
        f"  pairs={summary['paired_count']} "
        f"unique_chunks={dataset['meta']['unique_chunks']} "
        f"avg_delta={summary['average_score_delta']:+.4f}"
    )


if __name__ == "__main__":
    main()
