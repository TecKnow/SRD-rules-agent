import argparse
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
import uuid
from collections.abc import Iterable, Iterator, Sequence
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from srd_eval.config import load_env
from srd_eval.io import ROOT, JsonObject, append_jsonl, read_jsonl, require_new_file, write_jsonl


DEFAULT_SOURCE_DIR = ROOT / "data" / "source" / "downfallx-dnd-5e-srd-markdown"
DEFAULT_RUNS_DIR = ROOT / "runs" / "rag"
DEFAULT_MODEL = "openai/text-embedding-3-small"
OPENROUTER_EMBEDDINGS_URL = "https://openrouter.ai/api/v1/embeddings"
SRD_VERSION = "5.2.1"
CHUNKING_STRATEGY = "markdown-headers-h1-h4-recursive-tiktoken-1200-100-v1"
EXCLUDED_MARKDOWN_NAMES = frozenset({"README.md", "CHANGELOG.md", "CONTRIBUTING.md"})
HEADERS_TO_SPLIT_ON = [
    ("#", "h1"),
    ("##", "h2"),
    ("###", "h3"),
    ("####", "h4"),
]


@dataclass(frozen=True, slots=True)
class ChunkConfig:
    source_dir: Path = DEFAULT_SOURCE_DIR
    chunk_size: int = 1200
    chunk_overlap: int = 100
    srd_version: str = SRD_VERSION


class OpenRouterEmbeddingsClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        app_name: str = "SRD rules agent RAG embeddings",
        site_url: str | None = None,
        timeout_seconds: int = 120,
    ) -> None:
        load_env()
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY is required for embedding calls")
        self.app_name = app_name
        self.site_url = site_url or os.environ.get("OPENROUTER_SITE_URL")
        self.timeout_seconds = timeout_seconds

    def embed_texts(self, *, model: str, texts: Sequence[str]) -> list[list[float]]:
        payload: JsonObject = {"model": model, "input": list(texts)}
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Title": self.app_name,
        }
        if self.site_url:
            headers["HTTP-Referer"] = self.site_url

        request = urllib.request.Request(
            OPENROUTER_EMBEDDINGS_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenRouter embedding request failed with HTTP {exc.code}: {body}") from exc

        try:
            data = raw["data"]
            embeddings = [item["embedding"] for item in data]
        except (KeyError, TypeError) as exc:
            raise RuntimeError(f"OpenRouter embedding response did not include embeddings: {raw}") from exc
        if len(embeddings) != len(texts):
            raise RuntimeError(f"Expected {len(texts)} embeddings, received {len(embeddings)}")
        return embeddings


def parse_args() -> argparse.Namespace:
    load_env()
    parser = argparse.ArgumentParser(description="Chunk and embed the SRD 5.2.1 markdown corpus.")
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--chunks-output", type=Path, default=None)
    parser.add_argument("--embeddings-output", type=Path, default=None)
    parser.add_argument("--model", default=os.environ.get("OPENROUTER_EMBEDDING_MODEL", DEFAULT_MODEL))
    parser.add_argument("--chunk-size", type=int, default=1200)
    parser.add_argument("--chunk-overlap", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--limit", type=int, default=None, help="Optional chunk limit for smoke tests.")
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--retry-delay-seconds", type=float, default=5.0)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--continue-on-error", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Validate chunking without writing or embedding.")
    parser.add_argument("--chunks-only", action="store_true", help="Write chunk JSONL without embedding.")
    return parser.parse_args()


def new_run_id() -> str:
    return f"srd-embeddings-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"


def resolve_output_dir(args: argparse.Namespace, run_id: str) -> Path:
    return args.output_dir or args.runs_dir / run_id


def markdown_files(source_dir: Path) -> list[Path]:
    if not source_dir.exists():
        raise FileNotFoundError(f"SRD markdown source directory does not exist: {source_dir}")
    return sorted(path for path in source_dir.glob("*.md") if path.name not in EXCLUDED_MARKDOWN_NAMES)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def slug(value: str) -> str:
    cleaned = []
    for char in value.lower():
        if char.isalnum():
            cleaned.append(char)
        elif cleaned and cleaned[-1] != "-":
            cleaned.append("-")
    return "".join(cleaned).strip("-") or "untitled"


def entity_type_for(source_file: str, metadata: JsonObject) -> str:
    name = str(metadata.get("h4") or metadata.get("h3") or metadata.get("h2") or metadata.get("h1") or "")
    lower_name = name.lower()
    match source_file:
        case "spells.md":
            return "spell" if name else "spell_section"
        case "monsters-A-Z.md" | "monsters.md" | "animals.md":
            return "monster" if name else "monster_section"
        case "magic-items.md":
            return "magic_item" if name else "magic_item_section"
        case "classes.md":
            return "class_feature" if name else "class_section"
        case "equipment.md":
            return "equipment"
        case "feats.md":
            return "feat"
        case "rules-glossary.md":
            if "[condition]" in lower_name:
                return "condition"
            if "[action]" in lower_name:
                return "action"
            return "glossary_entry" if name else "glossary_section"
        case _:
            return "rule_section"


def metadata_name(metadata: JsonObject, fallback: str) -> str:
    for key in ("h4", "h3", "h2", "h1"):
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return fallback


def make_chunk_id(source_file: str, name: str, text: str, chunk_index: int) -> str:
    digest = sha256_text(text)[:12]
    return f"{source_file}::{slug(name)}::{chunk_index:04d}::{digest}"


def split_markdown_file(path: Path, config: ChunkConfig, text_splitter: RecursiveCharacterTextSplitter) -> list[JsonObject]:
    source_text = path.read_text(encoding="utf-8")
    header_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=HEADERS_TO_SPLIT_ON, strip_headers=False)
    header_docs = header_splitter.split_text(source_text)
    records: list[JsonObject] = []

    for header_doc in header_docs:
        child_docs = text_splitter.split_documents([header_doc])
        for child_doc in child_docs:
            text = child_doc.page_content.strip()
            if not text:
                continue
            metadata: JsonObject = dict(child_doc.metadata)
            name = metadata_name(metadata, path.stem)
            chunk_index = len(records)
            metadata.update(
                {
                    "source_file": path.name,
                    "source_path": str(path.relative_to(ROOT).as_posix()) if path.is_relative_to(ROOT) else str(path),
                    "srd_version": config.srd_version,
                    "entity_type": entity_type_for(path.name, metadata),
                    "name": name,
                    "chunk_index": chunk_index,
                    "content_sha256": sha256_text(text),
                    "chunking_strategy": CHUNKING_STRATEGY,
                }
            )
            chunk_id = make_chunk_id(path.name, name, text, chunk_index)
            metadata["chunk_id"] = chunk_id
            records.append({"id": chunk_id, "text": text, "metadata": metadata})
    return records


def chunk_corpus(config: ChunkConfig) -> list[JsonObject]:
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        model_name="text-embedding-3-small",
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
    )
    chunks: list[JsonObject] = []
    for path in markdown_files(config.source_dir):
        chunks.extend(split_markdown_file(path, config, text_splitter))
    return chunks


def completed_embedding_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {
        str(row["id"])
        for row in read_jsonl(path)
        if row.get("id") and row.get("embedding") and not row.get("error")
    }


def batched(items: Sequence[JsonObject], batch_size: int) -> Iterator[list[JsonObject]]:
    if batch_size < 1:
        raise ValueError("--batch-size must be at least 1")
    for index in range(0, len(items), batch_size):
        yield list(items[index : index + batch_size])


def embed_batch_with_retries(
    client: OpenRouterEmbeddingsClient,
    *,
    batch: Sequence[JsonObject],
    model: str,
    retries: int,
    retry_delay_seconds: float,
) -> list[list[float]]:
    attempts = retries + 1
    for attempt in range(1, attempts + 1):
        try:
            return client.embed_texts(model=model, texts=[str(row["text"]) for row in batch])
        except Exception:
            if attempt >= attempts:
                raise
            time.sleep(retry_delay_seconds)
    raise AssertionError("unreachable retry loop exit")


def embedding_record(chunk: JsonObject, embedding: list[float], model: str) -> JsonObject:
    return {
        "id": chunk["id"],
        "text": chunk["text"],
        "metadata": chunk["metadata"],
        "embedding": embedding,
        "embedding_model": model,
        "embedding_dimensions": len(embedding),
        "embedded_at": datetime.now(UTC).isoformat(),
    }


def embedding_error_record(chunk: JsonObject, model: str, error: Exception) -> JsonObject:
    return {
        "id": chunk["id"],
        "text": chunk["text"],
        "metadata": chunk["metadata"],
        "embedding": [],
        "embedding_model": model,
        "embedding_dimensions": 0,
        "error": str(error),
        "embedded_at": datetime.now(UTC).isoformat(),
    }


def write_chunks(path: Path, chunks: Iterable[JsonObject]) -> int:
    return write_jsonl(path, chunks)


def embed_chunks(
    *,
    chunks: Sequence[JsonObject],
    output_path: Path,
    model: str,
    client: OpenRouterEmbeddingsClient,
    resume: bool,
    workers: int,
    batch_size: int,
    retries: int,
    retry_delay_seconds: float,
    continue_on_error: bool,
) -> tuple[int, int]:
    if workers < 1:
        raise ValueError("--workers must be at least 1")

    completed_ids = completed_embedding_ids(output_path) if resume else set()
    pending = [chunk for chunk in chunks if str(chunk["id"]) not in completed_ids]
    skipped = len(chunks) - len(pending)
    written = 0

    batches = list(batched(pending, batch_size))
    if not batches:
        return written, skipped

    with ThreadPoolExecutor(max_workers=workers) as executor:
        batch_iter = iter(batches)
        futures: dict[Future[list[list[float]]], list[JsonObject]] = {}

        def submit_next() -> bool:
            try:
                batch = next(batch_iter)
            except StopIteration:
                return False
            future = executor.submit(
                embed_batch_with_retries,
                client,
                batch=batch,
                model=model,
                retries=retries,
                retry_delay_seconds=retry_delay_seconds,
            )
            futures[future] = batch
            return True

        for _ in range(min(workers, len(batches))):
            submit_next()

        while futures:
            done, _ = wait(futures, return_when=FIRST_COMPLETED)
            for future in done:
                batch = futures.pop(future)
                try:
                    embeddings = future.result()
                    for chunk, embedding in zip(batch, embeddings, strict=True):
                        append_jsonl(output_path, embedding_record(chunk, embedding, model))
                        written += 1
                except Exception as exc:
                    if not continue_on_error:
                        for pending_future in futures:
                            pending_future.cancel()
                        raise RuntimeError(
                            "Embedding failed; re-run with --resume after fixing the issue. "
                            "Use --continue-on-error to record failures and keep going."
                        ) from exc
                    for chunk in batch:
                        append_jsonl(output_path, embedding_error_record(chunk, model, exc))
                        written += 1
                submit_next()

    return written, skipped


def summarize_chunks(chunks: Sequence[JsonObject]) -> JsonObject:
    by_file: dict[str, int] = {}
    max_chars = 0
    max_chunk_id = ""
    for chunk in chunks:
        source_file = str(chunk["metadata"]["source_file"])
        by_file[source_file] = by_file.get(source_file, 0) + 1
        length = len(str(chunk["text"]))
        if length > max_chars:
            max_chars = length
            max_chunk_id = str(chunk["id"])
    return {
        "chunks": len(chunks),
        "source_files": len(by_file),
        "chunks_by_file": dict(sorted(by_file.items())),
        "largest_chunk_chars": max_chars,
        "largest_chunk_id": max_chunk_id,
    }


def run(args: argparse.Namespace) -> JsonObject:
    config = ChunkConfig(source_dir=args.source_dir, chunk_size=args.chunk_size, chunk_overlap=args.chunk_overlap)
    chunks = chunk_corpus(config)
    if args.limit is not None:
        chunks = chunks[: args.limit]
    summary = summarize_chunks(chunks)

    if args.dry_run:
        return {"mode": "dry-run", **summary}

    run_id = args.run_id or new_run_id()
    output_dir = resolve_output_dir(args, run_id)
    chunks_output = args.chunks_output or output_dir / "chunks.jsonl"
    embeddings_output = args.embeddings_output or output_dir / "embeddings.jsonl"

    chunk_count = write_chunks(chunks_output, chunks)
    if args.chunks_only:
        return {"mode": "chunks-only", "chunks_output": str(chunks_output), "written_chunks": chunk_count, **summary}

    if not args.resume:
        require_new_file(embeddings_output)
    client = OpenRouterEmbeddingsClient(timeout_seconds=args.timeout_seconds)
    written, skipped = embed_chunks(
        chunks=chunks,
        output_path=embeddings_output,
        model=args.model,
        client=client,
        resume=args.resume,
        workers=args.workers,
        batch_size=args.batch_size,
        retries=args.retries,
        retry_delay_seconds=args.retry_delay_seconds,
        continue_on_error=args.continue_on_error,
    )
    return {
        "mode": "embed",
        "chunks_output": str(chunks_output),
        "embeddings_output": str(embeddings_output),
        "written_embeddings": written,
        "skipped_embeddings": skipped,
        "embedding_model": args.model,
        **summary,
    }


def main() -> None:
    args = parse_args()
    summary = run(args)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
