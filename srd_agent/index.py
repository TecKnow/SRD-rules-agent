"""Signature-keyed local Chroma index over the SRD markdown corpus.

Chunking is reused verbatim from the research pipeline
(``srd_rag.embed_srd.chunk_corpus``); only the *embedding* differs (local encoder
instead of the OpenRouter API). Each (encoder + chunker) combination gets its own
persistent Chroma collection under ``runs/agent/<signature>/`` so the bake-off can
hold several indexes side by side and rebuilds happen only when inputs change.
"""

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from srd_rag.embed_srd import ChunkConfig, chunk_corpus

from .config import AGENT_RUNS_DIR, DEFAULT_SRD_SOURCE_DIR, SRD_VERSION, EncoderSpec
from .retrieval import Encoder, build_encoder

CHROMA_DIRNAME = "chroma"
MANIFEST_NAME = "manifest.json"


@dataclass(slots=True)
class IndexManifest:
    signature: str
    encoder_id: str
    chunk_count: int
    chunk_size: int
    chunk_overlap: int
    srd_version: str
    collection_name: str
    chroma_dir: str


def _slug(value: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in value).strip("_").lower() or "encoder"


def collection_name(encoder: EncoderSpec) -> str:
    return f"srd_{SRD_VERSION.replace('.', '_')}_{_slug(encoder.id)}"[:60]


def index_signature(chunks: list[dict[str, Any]], encoder: EncoderSpec, config: ChunkConfig) -> str:
    """Hash inputs + config so a changed corpus/chunker/encoder invalidates cleanly.

    Chunk ids already embed a per-chunk content digest and the fixed chunking
    strategy, so hashing the sorted id set captures source revision + chunker.
    """
    payload = {
        "encoder": encoder.id,
        "document_prefix": encoder.document_prefix,
        "chunk_size": config.chunk_size,
        "chunk_overlap": config.chunk_overlap,
        "srd_version": config.srd_version,
        "chunk_count": len(chunks),
        "chunk_ids": sorted(str(c["id"]) for c in chunks),
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return digest[:16]


def _chroma_metadata(metadata: dict[str, Any]) -> dict[str, str | int | float | bool | None]:
    safe: dict[str, str | int | float | bool | None] = {}
    for key, value in metadata.items():
        safe[key] = value if isinstance(value, str | int | float | bool) or value is None else str(value)
    return safe


def _read_manifest(run_dir: Path) -> IndexManifest | None:
    path = run_dir / MANIFEST_NAME
    if not path.exists():
        return None
    return IndexManifest(**json.loads(path.read_text(encoding="utf-8")))


def prepare_index(
    encoder_spec: EncoderSpec,
    *,
    source_dir: Path = DEFAULT_SRD_SOURCE_DIR,
    runs_dir: Path = AGENT_RUNS_DIR,
    chunk_size: int = 1200,
    chunk_overlap: int = 100,
    batch_size: int = 64,
    limit: int | None = None,
    rebuild: bool = False,
    encoder: Encoder | None = None,
) -> tuple[Any, IndexManifest]:
    """Build (or load) the Chroma collection for ``encoder_spec``; idempotent.

    Returns the ready-to-query collection and its manifest. Re-running with the same
    inputs is a no-op (cache hit) unless ``rebuild=True``.
    """
    import chromadb

    config = ChunkConfig(source_dir=source_dir, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = chunk_corpus(config)
    if limit is not None:
        chunks = chunks[:limit]
    if not chunks:
        raise RuntimeError(f"No SRD chunks produced from {source_dir}")

    signature = index_signature(chunks, encoder_spec, config)
    run_dir = runs_dir / signature
    chroma_dir = run_dir / CHROMA_DIRNAME
    name = collection_name(encoder_spec)

    if rebuild and chroma_dir.exists():
        import shutil

        shutil.rmtree(chroma_dir)

    chroma_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(chroma_dir))
    collection = client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})

    manifest = IndexManifest(
        signature=signature,
        encoder_id=encoder_spec.id,
        chunk_count=len(chunks),
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        srd_version=config.srd_version,
        collection_name=name,
        chroma_dir=str(chroma_dir),
    )

    if not rebuild and collection.count() >= len(chunks) and _read_manifest(run_dir) is not None:
        return collection, manifest  # cache hit

    enc = encoder or build_encoder(encoder_spec)
    print(f"Embedding {len(chunks)} chunks with {encoder_spec.id} -> {name}", flush=True)
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start : start + batch_size]
        vectors = enc.embed_documents([str(c["text"]) for c in batch])
        collection.upsert(  # upsert so a re-run after a partial build is safe
            ids=[str(c["id"]) for c in batch],
            documents=[str(c["text"]) for c in batch],
            embeddings=vectors,
            metadatas=[_chroma_metadata(dict(c["metadata"])) for c in batch],
        )
        print(f"  embedded {min(start + batch_size, len(chunks))}/{len(chunks)}", flush=True)

    (run_dir / MANIFEST_NAME).write_text(
        json.dumps(asdict(manifest), indent=2, sort_keys=True), encoding="utf-8"
    )
    return collection, manifest
