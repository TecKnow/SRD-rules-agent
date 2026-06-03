import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from .config import load_env
from .io import DEFAULT_BENCHMARK_PATH, JsonObject, read_jsonl, require_new_file, write_jsonl
from .openrouter import OpenRouterClient


EVALUATOR_NAME = "deepeval-srd-correctness"
EVALUATOR_VERSION = "v2-structured-diagnostics"
DEFAULT_THRESHOLD = 0.7
REQUIRED_ANSWER_FIELDS = ("run_id", "question_id", "question", "answer", "model")
type FailureType = Literal[
    "edition_drift",
    "other_system_bleed",
    "non_srd_2024_import",
    "unsupported_citation",
    "false_srd_exclusion",
    "missed_limiting_phrase",
    "rule_name_collision",
    "overconfident_ambiguous_ruling",
    "insufficient_or_vague_answer",
]
FAILURE_TYPES: tuple[FailureType, ...] = (
    "edition_drift",
    "other_system_bleed",
    "non_srd_2024_import",
    "unsupported_citation",
    "false_srd_exclusion",
    "missed_limiting_phrase",
    "rule_name_collision",
    "overconfident_ambiguous_ruling",
    "insufficient_or_vague_answer",
)
FAILURE_TYPE_DESCRIPTIONS: dict[FailureType, str] = {
    "edition_drift": "Imports older D&D 2014 or other edition rules instead of SRD 5.2.1.",
    "other_system_bleed": "Imports Pathfinder, other games, forum lore, or non-D&D rules.",
    "non_srd_2024_import": "Treats non-SRD 2024 material as if it were in SRD 5.2.1.",
    "unsupported_citation": "Invents, overstates, or relies on unsupported citations or source claims.",
    "false_srd_exclusion": "Incorrectly says a real SRD 5.2.1 rule, option, item, spell, or feature is absent.",
    "missed_limiting_phrase": "Misses a material condition, exception, timing limit, action type, or scope limit.",
    "rule_name_collision": "Confuses similarly named rules, actions, spells, traits, features, or conditions.",
    "overconfident_ambiguous_ruling": "For an ambiguous benchmark row, forces one answer without preserving ambiguity.",
    "insufficient_or_vague_answer": "Is too vague, incomplete, hedged, or noncommittal to answer the question.",
}


def parse_args() -> argparse.Namespace:
    load_env()
    parser = argparse.ArgumentParser(description="Grade saved no-RAG answers with DeepEval.")
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK_PATH)
    parser.add_argument("--answers", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--limit", type=int, default=None, help="Optional smoke-test record limit.")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    parser.add_argument("--judge-model", default=os.environ.get("DEEPEVAL_JUDGE_MODEL", "gpt-4.1"))
    parser.add_argument(
        "--judge-provider",
        choices=["deepeval", "openrouter"],
        default=os.environ.get("DEEPEVAL_JUDGE_PROVIDER", "deepeval"),
        help="Use DeepEval's native model string or an OpenRouter-backed custom judge.",
    )
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--fail-fast", action="store_true")
    return parser.parse_args()


def default_output_path(answers_path: Path) -> Path:
    stem = answers_path.stem or "answers"
    return answers_path.with_name(f"{stem}.deepeval_scores.jsonl")


def benchmark_by_id(path: Path) -> dict[str, JsonObject]:
    return {str(row["id"]): row for row in read_jsonl(path)}


def expected_output(row: JsonObject) -> str:
    parts = [
        ("Expected answer", row.get("ai_refined_expected_answer") or row.get("expected_answer")),
        ("Rubric", row.get("ai_refined_rubric") or row.get("rubric")),
        ("Failure modes", row.get("failure_modes")),
        ("Common wrong answers", row.get("common_wrong_answers")),
        ("Alternative interpretations", row.get("alternative_interpretations")),
        ("Answer status", row.get("answer_status")),
        ("Authority evidence", row.get("authority_evidence")),
        ("SRD passages", row.get("srd_passages")),
        ("Gold answer", row.get("gold_answer_verbatim")),
    ]
    return "\n\n".join(f"{label}:\n{value}" for label, value in parts if value)


def validate_answers(answers: list[JsonObject], benchmark: dict[str, JsonObject]) -> None:
    errors: list[str] = []
    seen_pairs: dict[tuple[str, str], int] = {}

    for index, answer in enumerate(answers, start=1):
        missing = [field for field in REQUIRED_ANSWER_FIELDS if field not in answer or answer[field] is None]
        if missing:
            errors.append(f"row {index}: missing required field(s): {', '.join(missing)}")

        if answer.get("error"):
            errors.append(f"row {index}: contains error: {answer['error']}")

        answer_text = answer.get("answer")
        if isinstance(answer_text, str) and not answer_text.strip():
            errors.append(f"row {index}: blank answer")

        question_id_value = answer.get("question_id")
        model_value = answer.get("model")
        if question_id_value is not None:
            question_id = str(question_id_value)
            if question_id not in benchmark:
                errors.append(f"row {index}: question_id {question_id!r} not found in benchmark")

            if model_value is not None:
                pair = (question_id, str(model_value))
                first_index = seen_pairs.get(pair)
                if first_index is None:
                    seen_pairs[pair] = index
                else:
                    errors.append(
                        f"row {index}: duplicate question/model pair {pair!r}; first seen on row {first_index}"
                    )

    if errors:
        detail = "\n- ".join(errors)
        raise ValueError(f"Answer preflight failed; refusing to grade unsafe workbook:\n- {detail}")


def diagnostic_prompt(*, answer: JsonObject, benchmark_row: JsonObject) -> str:
    failure_types = "\n".join(
        f"- {name}: {FAILURE_TYPE_DESCRIPTIONS[name]}" for name in FAILURE_TYPES
    )
    return f"""You are grading a model answer to a D&D SRD 5.2.1 rules benchmark.

Use only the grading key below. Do not require exact wording. Reward correct rules conclusions, important limits and exceptions, and ambiguity preservation when the benchmark says the answer is ambiguous.
Penalize D&D 2014 drift, Pathfinder or other-system bleed, non-SRD 2024 imports, unsupported citations, false SRD exclusions, missed limiting phrases, rule-name collisions, and overconfident rulings on ambiguous rows.

Return only a JSON object with this exact shape:
{{
  "score": 0.0,
  "rationale": "one concise paragraph",
  "failure_types": {{
    "edition_drift": false,
    "other_system_bleed": false,
    "non_srd_2024_import": false,
    "unsupported_citation": false,
    "false_srd_exclusion": false,
    "missed_limiting_phrase": false,
    "rule_name_collision": false,
    "overconfident_ambiguous_ruling": false,
    "insufficient_or_vague_answer": false
  }},
  "failure_notes": {{
    "edition_drift": "",
    "other_system_bleed": "",
    "non_srd_2024_import": "",
    "unsupported_citation": "",
    "false_srd_exclusion": "",
    "missed_limiting_phrase": "",
    "rule_name_collision": "",
    "overconfident_ambiguous_ruling": "",
    "insufficient_or_vague_answer": ""
  }},
  "diagnostic_confidence": "high"
}}

Score is a float from 0.0 to 1.0. Set a failure type to true only when that error is present in the actual answer. Leave notes blank for false failure types. diagnostic_confidence must be "high", "medium", or "low".

Failure type definitions:
{failure_types}

Question:
{answer["question"]}

Actual answer:
{answer["answer"]}

Grading key:
{expected_output(benchmark_row)}
"""


def parse_judge_json(text: str) -> JsonObject:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Judge response was not valid JSON: {text}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"Judge response must be a JSON object: {value!r}")
    return value


def normalize_failure_types(value: Any) -> dict[FailureType, bool]:
    if not isinstance(value, dict):
        value = {}
    return {name: bool(value.get(name, False)) for name in FAILURE_TYPES}


def normalize_failure_notes(value: Any, failure_types: dict[FailureType, bool]) -> dict[FailureType, str]:
    if not isinstance(value, dict):
        value = {}
    return {
        name: str(value.get(name, "")).strip() if failure_types[name] else ""
        for name in FAILURE_TYPES
    }


def normalize_diagnostic_result(value: JsonObject) -> JsonObject:
    try:
        score = float(value["score"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Judge response did not include numeric score: {value!r}") from exc
    score = max(0.0, min(1.0, score))

    failure_types = normalize_failure_types(value.get("failure_types"))
    confidence = str(value.get("diagnostic_confidence", "medium")).strip().lower()
    if confidence not in {"high", "medium", "low"}:
        confidence = "medium"

    return {
        "score": score,
        "rationale": str(value.get("rationale", "")).strip(),
        "failure_types": failure_types,
        "failure_notes": normalize_failure_notes(value.get("failure_notes"), failure_types),
        "diagnostic_confidence": confidence,
    }


class StructuredOpenRouterJudge:
    def __init__(self, *, model: str, timeout_seconds: int) -> None:
        self.model = model
        self.client = OpenRouterClient(timeout_seconds=timeout_seconds)

    def measure(self, *, answer: JsonObject, benchmark_row: JsonObject) -> JsonObject:
        result = self.client.chat(
            model=self.model,
            messages=[{"role": "user", "content": diagnostic_prompt(answer=answer, benchmark_row=benchmark_row)}],
            temperature=0.0,
            max_tokens=1800,
            response_format={"type": "json_object"},
        )
        return normalize_diagnostic_result(parse_judge_json(result.text))


def make_judge(args: argparse.Namespace) -> StructuredOpenRouterJudge:
    if args.judge_provider != "openrouter":
        raise ValueError("Structured diagnostic grading currently requires --judge-provider openrouter")
    return StructuredOpenRouterJudge(model=args.judge_model, timeout_seconds=args.timeout_seconds)


def score_records(args: argparse.Namespace) -> tuple[Path, list[JsonObject]]:
    path = args.output or default_output_path(args.answers)
    require_new_file(path)

    benchmark = benchmark_by_id(args.benchmark)
    all_answers = list(read_jsonl(args.answers))
    validate_answers(all_answers, benchmark)

    judge = make_judge(args)
    answers = all_answers
    if args.limit is not None:
        answers = answers[: args.limit]

    rows: list[JsonObject] = []
    for answer in answers:
        question_id = str(answer["question_id"])
        benchmark_row = benchmark[question_id]

        try:
            result = judge.measure(answer=answer, benchmark_row=benchmark_row)
            score = float(result["score"])
            rows.append(
                {
                    "run_id": answer["run_id"],
                    "pipeline": answer.get("pipeline", "no_rag"),
                    "question_id": question_id,
                    "model": answer["model"],
                    "evaluator": EVALUATOR_NAME,
                    "evaluator_version": EVALUATOR_VERSION,
                    "judge_model": args.judge_model,
                    "judge_provider": args.judge_provider,
                    "threshold": args.threshold,
                    "score": score,
                    "passed": score >= args.threshold,
                    "rationale": result["rationale"],
                    "failure_types": result["failure_types"],
                    "failure_notes": result["failure_notes"],
                    "diagnostic_confidence": result["diagnostic_confidence"],
                    "question_metadata": answer.get("benchmark_metadata", {}),
                    "graded_at": datetime.now(UTC).isoformat(),
                }
            )
        except Exception as exc:
            if args.fail_fast:
                raise
            rows.append(error_record(answer, args, str(exc)))

    return path, rows


def error_record(answer: JsonObject, args: argparse.Namespace, error: str) -> JsonObject:
    return {
        "run_id": answer.get("run_id"),
        "pipeline": answer.get("pipeline", "no_rag"),
        "question_id": str(answer.get("question_id")),
        "model": answer.get("model"),
        "evaluator": EVALUATOR_NAME,
        "evaluator_version": EVALUATOR_VERSION,
        "judge_model": args.judge_model,
        "judge_provider": args.judge_provider,
        "threshold": args.threshold,
        "score": None,
        "passed": False,
        "rationale": None,
        "error": error,
        "graded_at": datetime.now(UTC).isoformat(),
    }


def main() -> None:
    args = parse_args()
    path, rows = score_records(args)
    count = write_jsonl(path, rows)
    print(f"Wrote {count} DeepEval score records to {path}")


if __name__ == "__main__":
    main()
