"""Retrieval bake-off: pick the encoder + reranker combo by measured quality.

For each candidate :class:`RetrievalConfig` this generates single-shot RAG answers
(retrieve -> format -> local Ollama answer) over the benchmark question set, then grades
them with the *existing* OpenRouter-backed judge (``srd_eval.grade_deepeval``) and prints
a ranked comparison. Single-shot (not the full agent loop) keeps results directly
comparable to the published RAG report, and isolates *retrieval* quality as the variable.

Run in the WSL agent venv (Ollama up; TEI up only for the bge/mxbai candidates; and
``OPENROUTER_API_KEY`` in ``.env`` for the judge):

    python -m srd_agent.bakeoff --candidate nomic-none --limit 20      # smoke
    python -m srd_agent.bakeoff --candidate nomic-none --candidate nomic-bge
"""

import argparse
import json
from pathlib import Path
from types import SimpleNamespace

from srd_eval.config import load_env
from srd_eval.grade_deepeval import score_records
from srd_eval.io import ROOT, DEFAULT_BENCHMARK_PATH, JsonObject, append_jsonl, read_jsonl, require_new_file

from .config import (
    AGENT_RUNS_DIR,
    BGE_M3_TEI,
    BGE_RERANK_TEI,
    DEFAULT_GEN_MODEL,
    DEFAULT_OPENAI_API_KEY,
    DEFAULT_OPENAI_BASE_URL,
    MXBAI_RERANK_TEI,
    NO_RERANK,
    NOMIC_OPENAI,
    GenSpec,
    RetrievalConfig,
)
from .agent import build_chat_model
from .index import prepare_index
from .retrieval import Retriever
from .tools import format_candidates

DEFAULT_QUESTIONS = ROOT / "Resources" / "Test files" / "questions_only.jsonl"
BAKEOFF_DIR = AGENT_RUNS_DIR / "bakeoff"

GEN_SYSTEM_PROMPT = """You answer questions about D&D SRD 5.2.1 rules.

Use only the supplied SRD 5.2.1 context for rules facts.
Do not import Pathfinder, D&D 2014, forum rulings, or non-SRD 2024 material.
When the supplied context is incomplete or ambiguous, say so plainly.
Do not cite page numbers or book sections. You may refer to supplied source names when helpful.
Keep the answer concise but complete enough to resolve the rules question."""

# Named candidates. TEI-backed ones require a running TEI/Infinity server.
CANDIDATES: dict[str, RetrievalConfig] = {
    "nomic-none": RetrievalConfig(NOMIC_OPENAI, NO_RERANK),
    "nomic-bge": RetrievalConfig(NOMIC_OPENAI, BGE_RERANK_TEI),
    "nomic-mxbai": RetrievalConfig(NOMIC_OPENAI, MXBAI_RERANK_TEI),
    "bgem3-none": RetrievalConfig(BGE_M3_TEI, NO_RERANK),
    "bgem3-bge": RetrievalConfig(BGE_M3_TEI, BGE_RERANK_TEI),
}


def parse_args() -> argparse.Namespace:
    load_env()
    parser = argparse.ArgumentParser(description="Bake off retrieval configs on the SRD benchmark.")
    parser.add_argument(
        "--candidate",
        action="append",
        dest="candidates",
        choices=sorted(CANDIDATES),
        help="Candidate name (repeatable). Default: nomic-none.",
    )
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS)
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK_PATH)
    parser.add_argument("--gen-model", default=DEFAULT_GEN_MODEL)
    parser.add_argument("--gen-backend", default="openai", choices=["openai", "ollama"])
    parser.add_argument("--base-url", default=DEFAULT_OPENAI_BASE_URL, help="OpenAI-compatible /v1 endpoint.")
    parser.add_argument("--api-key", default=DEFAULT_OPENAI_API_KEY)
    parser.add_argument("--out-dir", type=Path, default=BAKEOFF_DIR)
    parser.add_argument("--limit", type=int, default=None, help="Smoke-test question limit.")
    parser.add_argument("--judge-model", default="openai/gpt-4.1")
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--num-ctx", type=int, default=8192)
    return parser.parse_args()


def generate_answers(name: str, config: RetrievalConfig, *, questions: list[JsonObject], llm, out_dir: Path) -> Path:
    collection, _ = prepare_index(config.encoder)
    retriever = Retriever.from_config(config, collection)
    answers_path = out_dir / name / "answers.jsonl"
    require_new_file(answers_path)
    print(f"[{name}] generating {len(questions)} answers ({config.id})", flush=True)
    for index, row in enumerate(questions, start=1):
        candidates = retriever.search(str(row["question"]))
        user = f"Question:\n{row['question']}\n\nSRD 5.2.1 context:\n{format_candidates(candidates)}"
        reply = llm.invoke([("system", GEN_SYSTEM_PROMPT), ("human", user)])
        append_jsonl(
            answers_path,
            {
                "run_id": f"bakeoff-{name}",
                "pipeline": "rag_bakeoff",
                "question_id": row["id"],
                "model": name,  # the bake-off groups by config name in the score table
                "question": row["question"],
                "answer": getattr(reply, "content", str(reply)),
                "benchmark_metadata": {"retrieval": config.id},
            },
        )
        if index % 10 == 0 or index == len(questions):
            print(f"  [{name}] {index}/{len(questions)}", flush=True)
    return answers_path


def grade(answers_path: Path, args: argparse.Namespace) -> Path:
    grade_args = SimpleNamespace(
        benchmark=args.benchmark,
        answers=answers_path,
        output=None,
        limit=None,
        threshold=0.7,
        judge_model=args.judge_model,
        judge_provider="openrouter",
        timeout_seconds=120,
        judge_max_tokens=4000,
        concurrency=args.concurrency,
        resume=False,
        retry_errors=False,
        fail_fast=False,
    )
    path, _ = score_records(grade_args)
    return path


def summarize(score_path: Path) -> dict[str, float]:
    scores = [row["score"] for row in read_jsonl(score_path) if row.get("score") is not None]
    passes = sum(1 for row in read_jsonl(score_path) if row.get("passed"))
    n = len(scores)
    return {"n": n, "avg_score": sum(scores) / n if n else 0.0, "passes": passes}


def main() -> None:
    args = parse_args()
    llm = build_chat_model(
        GenSpec(
            backend=args.gen_backend,
            model=args.gen_model,
            base_url=args.base_url,
            api_key=args.api_key,
            temperature=args.temperature,
            num_ctx=args.num_ctx,
        )
    )
    questions = list(read_jsonl(args.questions))
    if args.limit is not None:
        questions = questions[: args.limit]

    names = args.candidates or ["nomic-none"]
    results: list[tuple[str, dict[str, float]]] = []
    for name in names:
        answers_path = generate_answers(name, CANDIDATES[name], questions=questions, llm=llm, out_dir=args.out_dir)
        score_path = grade(answers_path, args)
        results.append((name, summarize(score_path)))

    results.sort(key=lambda item: item[1]["avg_score"], reverse=True)
    print("\n=== Bake-off results (ranked by avg judged score) ===")
    print(f"{'candidate':<14} {'retrieval':<46} {'n':>4} {'avg':>6} {'pass':>5}")
    for name, summary in results:
        print(
            f"{name:<14} {CANDIDATES[name].id:<46} {summary['n']:>4} "
            f"{summary['avg_score']:>6.3f} {summary['passes']:>5}"
        )
    (args.out_dir / "summary.json").write_text(
        json.dumps({name: summary for name, summary in results}, indent=2, sort_keys=True),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
