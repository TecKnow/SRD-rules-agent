import argparse
import os
import threading
import time
import uuid
from collections.abc import Mapping, Sequence
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from srd_rag.embed_srd import DEFAULT_MODEL as DEFAULT_EMBEDDING_MODEL
from srd_rag.embed_srd import OpenRouterEmbeddingsClient

from .config import load_env
from .gather_no_rag import completed_pairs, existing_run_id, models_from_args
from .io import ROOT, JsonObject, append_jsonl, compact_metadata, read_jsonl, require_new_file
from .openrouter import OpenRouterClient


PROMPT_VERSION = "rag-chroma-v1"
PIPELINE = "rag_chroma"
DEFAULT_QUESTIONS_PATH = ROOT / "Resources" / "Test files" / "questions_only.jsonl"
DEFAULT_RUNS_DIR = ROOT / "runs" / "rag"
DEFAULT_EMBEDDINGS_PATH = ROOT / "runs" / "rag" / "srd-5-2-1-openrouter-text-embedding-3-small" / "embeddings.jsonl"
DEFAULT_CHROMA_DIR = ROOT / "runs" / "rag" / "srd-5-2-1-openrouter-text-embedding-3-small" / "chroma"
DEFAULT_COLLECTION_NAME = "srd_5_2_1_text_embedding_3_small"

SYSTEM_PROMPT = """You answer questions about D&D SRD 5.2.1 rules.

Use only the supplied SRD 5.2.1 context for rules facts.
Do not import Pathfinder, D&D 2014, forum rulings, or non-SRD 2024 material.
When the supplied context is incomplete or ambiguous, say so plainly.
Do not cite page numbers or book sections. You may refer to supplied source names when helpful.
Keep the answer concise but complete enough to resolve the rules question."""


def parse_args() -> argparse.Namespace:
    load_env()
    parser = argparse.ArgumentParser(description="Gather Chroma RAG model answers for the SRD benchmark.")
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS_PATH)
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--embeddings", type=Path, default=DEFAULT_EMBEDDINGS_PATH)
    parser.add_argument("--chroma-dir", type=Path, default=DEFAULT_CHROMA_DIR)
    parser.add_argument("--collection-name", default=DEFAULT_COLLECTION_NAME)
    parser.add_argument("--embedding-model", default=os.environ.get("OPENROUTER_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL))
    parser.add_argument("--top-k", type=int, default=6)
    parser.add_argument("--model", action="append", dest="models", help="OpenRouter model id. Repeat for multiple models.")
    parser.add_argument("--limit", type=int, default=None, help="Optional smoke-test row limit.")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=1600)
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--resume", action="store_true", help="Append to an existing output and skip completed answers.")
    parser.add_argument("--retries", type=int, default=2, help="Retries for transient request failures.")
    parser.add_argument("--retry-delay-seconds", type=float, default=5.0)
    parser.add_argument("--continue-on-error", action="store_true", help="Record failed requests and keep going.")
    return parser.parse_args()


def new_run_id() -> str:
    return f"rag-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"


def output_path(args: argparse.Namespace, run_id: str) -> Path:
    if args.output:
        return args.output
    return args.runs_dir / run_id / "answers.jsonl"


def resolve_run(args: argparse.Namespace) -> tuple[str, Path]:
    if args.resume and not args.run_id and not args.output:
        raise RuntimeError("--resume requires --run-id or --output")
    provisional_run_id = args.run_id or new_run_id()
    path = output_path(args, provisional_run_id)
    if args.resume:
        return args.run_id or existing_run_id(path) or provisional_run_id, path
    require_new_file(path)
    return provisional_run_id, path


def chroma_metadata(metadata: Mapping[str, Any]) -> dict[str, str | int | float | bool | None]:
    safe: dict[str, str | int | float | bool | None] = {}
    for key, value in metadata.items():
        if isinstance(value, str | int | float | bool) or value is None:
            safe[key] = value
        else:
            safe[key] = str(value)
    return safe


def collection_count(collection: Any) -> int:
    count = getattr(collection, "count")
    return int(count())


def load_embedding_rows(path: Path) -> list[JsonObject]:
    rows = []
    for row in read_jsonl(path):
        if row.get("embedding") and not row.get("error"):
            rows.append(row)
    if not rows:
        raise RuntimeError(f"No successful embedding records found in {path}")
    return rows


def batched(items: Sequence[JsonObject], batch_size: int) -> list[list[JsonObject]]:
    return [list(items[index : index + batch_size]) for index in range(0, len(items), batch_size)]


def get_or_build_collection(*, chroma_dir: Path, collection_name: str, embeddings_path: Path) -> Any:
    try:
        import chromadb
    except ImportError as exc:
        raise RuntimeError("chromadb is required. Run `uv sync` before gathering RAG answers.") from exc

    chroma_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(chroma_dir))
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )
    if collection_count(collection) > 0:
        return collection

    rows = load_embedding_rows(embeddings_path)
    print(f"Building Chroma collection {collection_name!r} from {len(rows)} embedding rows...", flush=True)
    for batch in batched(rows, 500):
        collection.add(
            ids=[str(row["id"]) for row in batch],
            documents=[str(row["text"]) for row in batch],
            embeddings=[row["embedding"] for row in batch],
            metadatas=[chroma_metadata(row.get("metadata", {})) for row in batch],
        )
    return collection


def retrieve_context(
    *,
    collection: Any,
    row: JsonObject,
    query_embedding: list[float],
    top_k: int,
) -> list[JsonObject]:
    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    ids = result.get("ids", [[]])[0]
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]
    retrieved = []
    for rank, (chunk_id, text, metadata, distance) in enumerate(zip(ids, documents, metadatas, distances, strict=True), start=1):
        retrieved.append(
            {
                "rank": rank,
                "chunk_id": chunk_id,
                "distance": distance,
                "metadata": dict(metadata or {}),
                "text": text,
            }
        )
    if not retrieved:
        raise RuntimeError(f"No RAG context retrieved for question {row['id']}")
    return retrieved


def source_label(item: JsonObject) -> str:
    metadata = item.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
    source_file = metadata.get("source_file", "unknown-source")
    name = metadata.get("name")
    if name and name != source_file:
        return f"{source_file} | {name}"
    return str(source_file)


def format_context(retrieved_context: Sequence[JsonObject]) -> str:
    blocks = []
    for item in retrieved_context:
        blocks.append(
            "\n".join(
                [
                    f"[{item['rank']}] {source_label(item)}",
                    str(item["text"]),
                ]
            )
        )
    return "\n\n---\n\n".join(blocks)


def make_user_prompt(row: JsonObject, retrieved_context: Sequence[JsonObject]) -> str:
    return f"""Question:
{row["question"]}

SRD 5.2.1 context:
{format_context(retrieved_context)}"""


def query_contexts(
    *,
    rows: Sequence[JsonObject],
    collection: Any,
    embedding_client: OpenRouterEmbeddingsClient,
    embedding_model: str,
    top_k: int,
) -> dict[str, list[JsonObject]]:
    contexts: dict[str, list[JsonObject]] = {}
    total = len(rows)
    for index, row in enumerate(rows, start=1):
        print(f"[retrieval {index}/{total}] {row['id']}", flush=True)
        embedding = embedding_client.embed_texts(model=embedding_model, texts=[str(row["question"])])[0]
        contexts[str(row["id"])] = retrieve_context(
            collection=collection,
            row=row,
            query_embedding=embedding,
            top_k=top_k,
        )
    return contexts


def chat_with_retries(
    client: OpenRouterClient,
    *,
    row: JsonObject,
    model: str,
    retrieved_context: Sequence[JsonObject],
    args: argparse.Namespace,
) -> JsonObject:
    attempts = args.retries + 1
    for attempt in range(1, attempts + 1):
        try:
            result = client.chat(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": make_user_prompt(row, retrieved_context)},
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


def make_answer_record(
    *,
    run_id: str,
    row: JsonObject,
    model: str,
    retrieved_context: Sequence[JsonObject],
    result: JsonObject,
    args: argparse.Namespace,
) -> JsonObject:
    return {
        "run_id": run_id,
        "pipeline": PIPELINE,
        "question_id": row["id"],
        "model": model,
        "prompt_version": PROMPT_VERSION,
        "question": row["question"],
        "answer": result["text"],
        "benchmark_metadata": compact_metadata(row),
        "rag": {
            "embedding_model": args.embedding_model,
            "embeddings_path": str(args.embeddings),
            "chroma_dir": str(args.chroma_dir),
            "collection_name": args.collection_name,
            "top_k": args.top_k,
            "retrieved_context": list(retrieved_context),
        },
        "raw_response": result["raw_response"],
        "generated_at": datetime.now(UTC).isoformat(),
    }


def make_error_record(
    *,
    run_id: str,
    row: JsonObject,
    model: str,
    retrieved_context: Sequence[JsonObject],
    error: Exception,
    args: argparse.Namespace,
) -> JsonObject:
    return {
        "run_id": run_id,
        "pipeline": PIPELINE,
        "question_id": row["id"],
        "model": model,
        "prompt_version": PROMPT_VERSION,
        "question": row["question"],
        "answer": "",
        "benchmark_metadata": compact_metadata(row),
        "rag": {
            "embedding_model": args.embedding_model,
            "embeddings_path": str(args.embeddings),
            "chroma_dir": str(args.chroma_dir),
            "collection_name": args.collection_name,
            "top_k": args.top_k,
            "retrieved_context": list(retrieved_context),
        },
        "raw_response": {},
        "error": str(error),
        "generated_at": datetime.now(UTC).isoformat(),
    }


def gather_pair(
    *,
    run_id: str,
    row: JsonObject,
    model: str,
    retrieved_context: Sequence[JsonObject],
    args: argparse.Namespace,
) -> JsonObject:
    client = OpenRouterClient(timeout_seconds=args.timeout_seconds)
    result = chat_with_retries(client, row=row, model=model, retrieved_context=retrieved_context, args=args)
    return make_answer_record(
        run_id=run_id,
        row=row,
        model=model,
        retrieved_context=retrieved_context,
        result=result,
        args=args,
    )


def gather_records(args: argparse.Namespace) -> tuple[Path, int]:
    if args.top_k < 1:
        raise ValueError("--top-k must be at least 1")
    if args.workers < 1:
        raise ValueError("--workers must be at least 1")

    run_id, path = resolve_run(args)
    models = models_from_args(args.models)
    rows = list(read_jsonl(args.questions))
    if args.limit is not None:
        rows = rows[: args.limit]

    complete = completed_pairs(path) if args.resume else set()
    collection = get_or_build_collection(
        chroma_dir=args.chroma_dir,
        collection_name=args.collection_name,
        embeddings_path=args.embeddings,
    )
    embedding_client = OpenRouterEmbeddingsClient(timeout_seconds=args.timeout_seconds)
    contexts = query_contexts(
        rows=rows,
        collection=collection,
        embedding_client=embedding_client,
        embedding_model=args.embedding_model,
        top_k=args.top_k,
    )

    planned_pairs = [(row, model) for row in rows for model in models]
    total = len(planned_pairs)
    written = 0
    skipped = 0
    write_lock = threading.Lock()

    print(f"Writing RAG answers to {path}", flush=True)
    print(f"Run id: {run_id}", flush=True)
    print(f"Planned requests: {total} ({len(rows)} questions x {len(models)} models)", flush=True)
    print(f"Answer workers: {args.workers}", flush=True)

    pending = []
    for index, (row, model) in enumerate(planned_pairs, start=1):
        pair = (str(row["id"]), model)
        if pair in complete:
            skipped += 1
            print(f"[{index}/{total}] SKIP {row['id']} | {model}", flush=True)
            continue
        pending.append((index, row, model))

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        pair_iter = iter(pending)
        futures: dict[Future[JsonObject], tuple[int, JsonObject, str]] = {}

        def submit_next() -> bool:
            try:
                index, row, model = next(pair_iter)
            except StopIteration:
                return False
            print(f"[{index}/{total}] START {row['id']} | {model}", flush=True)
            future = executor.submit(
                gather_pair,
                run_id=run_id,
                row=row,
                model=model,
                retrieved_context=contexts[str(row["id"])],
                args=args,
            )
            futures[future] = (index, row, model)
            return True

        for _ in range(min(args.workers, len(pending))):
            submit_next()

        while futures:
            done, _ = wait(futures, return_when=FIRST_COMPLETED)
            for future in done:
                index, row, model = futures.pop(future)
                try:
                    record = future.result()
                    with write_lock:
                        append_jsonl(path, record)
                    written += 1
                    print(f"[{index}/{total}] DONE  {row['id']} | {model}", flush=True)
                except Exception as exc:
                    with write_lock:
                        append_jsonl(
                            path,
                            make_error_record(
                                run_id=run_id,
                                row=row,
                                model=model,
                                retrieved_context=contexts[str(row["id"])],
                                error=exc,
                                args=args,
                            ),
                        )
                    written += 1
                    print(f"[{index}/{total}] ERROR {row['id']} | {model}: {exc}", flush=True)
                    if not args.continue_on_error:
                        for pending_future in futures:
                            pending_future.cancel()
                        print("Stopping after error. Re-run with --resume to continue after fixing the issue.", flush=True)
                        raise SystemExit(1)
                submit_next()

    print(f"Finished. Appended {written} record(s), skipped {skipped} completed request(s).", flush=True)
    return path, written


def main() -> None:
    args = parse_args()
    path, count = gather_records(args)
    print(f"Wrote {count} RAG answer records to {path}")


if __name__ == "__main__":
    main()
