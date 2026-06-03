from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .io import DEFAULT_BENCHMARK_PATH, read_jsonl, require_new_file, write_jsonl
from .openrouter import OpenRouterClient


EVALUATOR_NAME = "deepeval-srd-correctness"
EVALUATOR_VERSION = "v1"
DEFAULT_THRESHOLD = 0.7


def parse_args() -> argparse.Namespace:
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


def benchmark_by_id(path: Path) -> dict[str, dict[str, Any]]:
    return {str(row["id"]): row for row in read_jsonl(path)}


def expected_output(row: dict[str, Any]) -> str:
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


def make_metric(*, model: Any, threshold: float) -> Any:
    from deepeval.metrics import GEval
    from deepeval.test_case import SingleTurnParams

    return GEval(
        name="SRD Rule Answer Correctness",
        criteria="""Evaluate whether the actual answer correctly answers the D&D SRD 5.2.1 question.

Use the expected answer, rubric, failure modes, authority evidence, SRD passages, and gold answer as the grading key.
Reward answers that reach the correct rules conclusion, preserve important limits and exceptions, and handle ambiguity when the benchmark says the answer is ambiguous.
Penalize answers that import D&D 2014, Pathfinder, forum lore, non-SRD 2024 material, unsupported citations, false SRD exclusions, or overconfident rulings.
Do not require exact wording. Grade source-grounded substance and rules reasoning.""",
        evaluation_params=[
            SingleTurnParams.INPUT,
            SingleTurnParams.ACTUAL_OUTPUT,
            SingleTurnParams.EXPECTED_OUTPUT,
        ],
        threshold=threshold,
        model=model,
    )


class OpenRouterDeepEvalModel:
    def __init__(self, *, model: str, timeout_seconds: int) -> None:
        from deepeval.models.base_model import DeepEvalBaseLLM

        class _Model(DeepEvalBaseLLM):
            def __init__(self, model_name: str, timeout: int) -> None:
                self.model_name = model_name
                self.client = OpenRouterClient(timeout_seconds=timeout)

            def load_model(self) -> OpenRouterClient:
                return self.client

            def get_model_name(self) -> str:
                return f"openrouter/{self.model_name}"

            def generate(self, prompt: str, schema: Any | None = None) -> Any:
                messages = [{"role": "user", "content": prompt}]
                result = self.client.chat(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.0,
                    max_tokens=2000,
                    response_format={"type": "json_object"} if schema else None,
                )
                if schema is None:
                    return result.text
                try:
                    return schema.model_validate_json(result.text)
                except Exception:
                    return schema.model_validate(json.loads(result.text))

            async def a_generate(self, prompt: str, schema: Any | None = None) -> Any:
                return self.generate(prompt, schema)

        self.instance = _Model(model, timeout_seconds)


def judge_model(args: argparse.Namespace) -> Any:
    if args.judge_provider == "openrouter":
        return OpenRouterDeepEvalModel(model=args.judge_model, timeout_seconds=args.timeout_seconds).instance
    return args.judge_model


def score_records(args: argparse.Namespace) -> tuple[Path, list[dict[str, Any]]]:
    from deepeval.test_case import LLMTestCase

    path = args.output or default_output_path(args.answers)
    require_new_file(path)

    benchmark = benchmark_by_id(args.benchmark)
    metric = make_metric(model=judge_model(args), threshold=args.threshold)
    answers = list(read_jsonl(args.answers))
    if args.limit is not None:
        answers = answers[: args.limit]

    rows: list[dict[str, Any]] = []
    for answer in answers:
        question_id = str(answer["question_id"])
        benchmark_row = benchmark.get(question_id)
        if benchmark_row is None:
            error = f"question_id {question_id!r} not found in benchmark"
            if args.fail_fast:
                raise KeyError(error)
            rows.append(error_record(answer, args, error))
            continue

        test_case = LLMTestCase(
            input=answer["question"],
            actual_output=answer["answer"],
            expected_output=expected_output(benchmark_row),
        )
        try:
            metric.measure(test_case)
            score = float(metric.score) if metric.score is not None else None
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
                    "passed": score is not None and score >= args.threshold,
                    "rationale": getattr(metric, "reason", None),
                    "question_metadata": answer.get("benchmark_metadata", {}),
                    "graded_at": datetime.now(UTC).isoformat(),
                }
            )
        except Exception as exc:
            if args.fail_fast:
                raise
            rows.append(error_record(answer, args, str(exc)))

    return path, rows


def error_record(answer: dict[str, Any], args: argparse.Namespace, error: str) -> dict[str, Any]:
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
