"""Retrieval bake-off: pick chunking / encoder / reranker by measured quality.

For each candidate :class:`RetrievalConfig` this generates single-shot RAG answers
(retrieve -> format -> local LLM answer) over the benchmark question set, then (optionally)
grades them with the existing OpenRouter-backed judge (``srd_eval.grade_deepeval``) and
prints a ranked comparison. Single-shot (not the full agent loop) keeps results directly
comparable to the published RAG report and isolates the *retrieval* variable.

Gathering answers is local and free (Ollama). Grading costs API credits, so the gather and
grade steps are separable: use ``--gather-only`` to produce judge-ready answer files and stop.

Run in the project venv (Ollama up; OPENROUTER_API_KEY in .env only for grading):

    # Chunking sweep, gather locally, stop before paid judging:
    python -m srd_agent.bakeoff --suite chunking --gather-only

    # Reranker sweep (needs a TEI server for the bge/mxbai candidates), gather + grade:
    python -m srd_agent.bakeoff --suite rerank
"""

import argparse
import json
import time
from pathlib import Path
from types import SimpleNamespace

from srd_eval.config import load_env
from srd_eval.grade_deepeval import score_records
from srd_eval.io import ROOT, DEFAULT_BENCHMARK_PATH, JsonObject, append_jsonl, read_jsonl

from .agent import build_chat_model
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

# Chunking sweep: vary only chunk size/overlap. No reranker (so chunk quality isn't masked),
# and top_k scaled so the retrieved-context token budget stays ~constant (~7.2k tokens) across
# configs -- this isolates chunk *granularity* from how much text the model sees.
# (fetch_k == top_k because NoOpReranker just takes the first top_k.)
CHUNK_SWEEP: dict[str, RetrievalConfig] = {
    "chunk-512": RetrievalConfig(NOMIC_OPENAI, NO_RERANK, fetch_k=14, top_k=14, chunk_size=512, chunk_overlap=64),
    "chunk-800": RetrievalConfig(NOMIC_OPENAI, NO_RERANK, fetch_k=9, top_k=9, chunk_size=800, chunk_overlap=100),
    "chunk-1200": RetrievalConfig(NOMIC_OPENAI, NO_RERANK, fetch_k=6, top_k=6, chunk_size=1200, chunk_overlap=100),
    "chunk-1600": RetrievalConfig(NOMIC_OPENAI, NO_RERANK, fetch_k=5, top_k=5, chunk_size=1600, chunk_overlap=160),
}

# Reranker sweep: fixed (baseline) chunking, vary the reranker. TEI-backed ones need a server.
RERANK_SWEEP: dict[str, RetrievalConfig] = {
    "rr-none": RetrievalConfig(NOMIC_OPENAI, NO_RERANK),
    "rr-bge": RetrievalConfig(NOMIC_OPENAI, BGE_RERANK_TEI),
    "rr-mxbai": RetrievalConfig(NOMIC_OPENAI, MXBAI_RERANK_TEI),
    "rr-bgem3enc-bge": RetrievalConfig(BGE_M3_TEI, BGE_RERANK_TEI),
}

CANDIDATES: dict[str, RetrievalConfig] = {**CHUNK_SWEEP, **RERANK_SWEEP}
SUITES: dict[str, list[str]] = {
    "chunking": list(CHUNK_SWEEP),
    "rerank": list(RERANK_SWEEP),
}


def parse_args() -> argparse.Namespace:
    load_env()
    parser = argparse.ArgumentParser(description="Bake off retrieval configs on the SRD benchmark.")
    parser.add_argument("--suite", choices=sorted(SUITES), help="Run a named candidate suite.")
    parser.add_argument(
        "--candidate",
        action="append",
        dest="candidates",
        choices=sorted(CANDIDATES),
        help="Candidate name (repeatable). Overrides --suite.",
    )
    parser.add_argument("--gather-only", action="store_true", help="Generate answers, skip the paid judging step.")
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS)
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK_PATH)
    parser.add_argument("--gen-model", default=DEFAULT_GEN_MODEL)
    parser.add_argument("--gen-backend", default="openai", choices=["openai", "ollama"])
    parser.add_argument("--base-url", default=DEFAULT_OPENAI_BASE_URL, help="OpenAI-compatible /v1 endpoint.")
    parser.add_argument("--api-key", default=DEFAULT_OPENAI_API_KEY)
    parser.add_argument("--out-dir", type=Path, default=BAKEOFF_DIR)
    parser.add_argument("--limit", type=int, default=None, help="Smoke-test question limit.")
    parser.add_argument("--judge-model", default="openai/gpt-4.1-mini")
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--num-ctx", type=int, default=8192)
    parser.add_argument("--retries", type=int, default=3, help="Per-question generation retries.")
    return parser.parse_args()


def _completed_question_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {str(r["question_id"]) for r in read_jsonl(path) if r.get("answer") and not r.get("error")}


def generate_answers(
    name: str,
    config: RetrievalConfig,
    *,
    questions: list[JsonObject],
    llm,
    out_dir: Path,
    retries: int = 3,
) -> Path:
    """Build the config's index, then gather single-shot answers. Resumable + retrying."""
    collection, _ = prepare_index(
        config.encoder, chunk_size=config.chunk_size, chunk_overlap=config.chunk_overlap
    )
    retriever = Retriever.from_config(config, collection)
    answers_path = out_dir / name / "answers.jsonl"
    done = _completed_question_ids(answers_path)
    pending = [row for row in questions if str(row["id"]) not in done]
    print(f"[{name}] {config.id}", flush=True)
    print(f"[{name}] {len(pending)} to generate ({len(done)} already done) -> {answers_path}", flush=True)

    for index, row in enumerate(pending, start=1):
        candidates = retriever.search(str(row["question"]))
        user = f"Question:\n{row['question']}\n\nSRD 5.2.1 context:\n{format_candidates(candidates)}"
        text = None
        for attempt in range(retries + 1):
            try:
                reply = llm.invoke([("system", GEN_SYSTEM_PROMPT), ("human", user)])
                text = getattr(reply, "content", str(reply))
                break
            except Exception as exc:
                if attempt >= retries:
                    raise RuntimeError(f"[{name}] generation failed for {row['id']}; re-run to resume") from exc
                time.sleep(3)
        append_jsonl(
            answers_path,
            {
                "run_id": f"bakeoff-{name}",
                "pipeline": "rag_bakeoff",
                "question_id": row["id"],
                "model": name,  # the bake-off groups by config name in the score table
                "question": row["question"],
                "answer": text,
                "benchmark_metadata": {"retrieval": config.id},
            },
        )
        if index % 10 == 0 or index == len(pending):
            print(f"  [{name}] {index}/{len(pending)}", flush=True)
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
    rows = list(read_jsonl(score_path))
    scores = [r["score"] for r in rows if r.get("score") is not None]
    passes = sum(1 for r in rows if r.get("passed"))
    n = len(scores)
    return {"n": n, "avg_score": sum(scores) / n if n else 0.0, "passes": passes}


def resolve_candidates(args: argparse.Namespace) -> list[str]:
    if args.candidates:
        return args.candidates
    if args.suite:
        return SUITES[args.suite]
    return ["chunk-1200"]


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

    names = resolve_candidates(args)
    print(f"Candidates: {names}  | questions: {len(questions)}  | gather-only: {args.gather_only}", flush=True)

    answer_paths: dict[str, Path] = {}
    for name in names:
        answer_paths[name] = generate_answers(
            name, CANDIDATES[name], questions=questions, llm=llm, out_dir=args.out_dir, retries=args.retries
        )

    if args.gather_only:
        print("\n=== Gathered answer sets (judge these yourself; grading uses API credits) ===")
        for name in names:
            print(f"  {name:<16} {CANDIDATES[name].id}")
            print(f"    answers: {answer_paths[name]}")
            print(f"    grade:   srd-eval-grade --answers {answer_paths[name]} --judge-provider openrouter --judge-model {args.judge_model}")
        (args.out_dir / "gather_manifest.json").write_text(
            json.dumps({n: {"id": CANDIDATES[n].id, "answers": str(answer_paths[n])} for n in names}, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return

    results: list[tuple[str, dict[str, float]]] = []
    for name in names:
        results.append((name, summarize(grade(answer_paths[name], args))))
    results.sort(key=lambda item: item[1]["avg_score"], reverse=True)
    print("\n=== Bake-off results (ranked by avg judged score) ===")
    print(f"{'candidate':<16} {'retrieval':<60} {'n':>4} {'avg':>6} {'pass':>5}")
    for name, summary in results:
        print(f"{name:<16} {CANDIDATES[name].id:<60} {summary['n']:>4} {summary['avg_score']:>6.3f} {summary['passes']:>5}")
    (args.out_dir / "summary.json").write_text(
        json.dumps({name: summary for name, summary in results}, indent=2, sort_keys=True), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
