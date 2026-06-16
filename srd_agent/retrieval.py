"""Pluggable retrieval: encoder -> Chroma vector search -> cross-encoder reranker.

The whole pipeline is selected by a :class:`~srd_agent.config.RetrievalConfig`, so the
bake-off and the live agent run identical retrieval code with only the config swapped.
Backends are constructed lazily so importing this module stays cheap and side-effect
free (no model servers are contacted until you call ``.search``).
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

import httpx

from .config import EncoderSpec, RerankerSpec, RetrievalConfig


@dataclass(slots=True)
class Candidate:
    """A retrieved SRD chunk, optionally rescored by a reranker."""

    chunk_id: str
    text: str
    metadata: dict[str, Any]
    distance: float | None = None  # Chroma vector distance (lower = closer)
    score: float | None = None  # reranker relevance score (higher = better)
    rank: int = 0


# --------------------------------------------------------------------------- #
# Encoders
# --------------------------------------------------------------------------- #
class Encoder(Protocol):
    """Turns text into vectors. Implementations honour the spec's task prefixes."""

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


@dataclass(slots=True)
class OllamaEncoder:
    spec: EncoderSpec
    timeout_seconds: float = 120.0

    def _embed(self, inputs: list[str]) -> list[list[float]]:
        base = (self.spec.base_url or "http://127.0.0.1:11434").rstrip("/")
        resp = httpx.post(
            f"{base}/api/embed",
            json={"model": self.spec.model, "input": inputs},
            timeout=self.timeout_seconds,
        )
        resp.raise_for_status()
        data = resp.json()
        embeddings = data.get("embeddings")
        if not embeddings or len(embeddings) != len(inputs):
            raise RuntimeError(f"Ollama embed returned {len(embeddings or [])} vectors for {len(inputs)} inputs")
        return embeddings

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        prefixed = [f"{self.spec.document_prefix}{text}" for text in texts]
        return self._embed(prefixed)

    def embed_query(self, text: str) -> list[float]:
        return self._embed([f"{self.spec.query_prefix}{text}"])[0]


@dataclass(slots=True)
class OpenAIEncoder:
    """Any OpenAI-compatible ``POST /v1/embeddings`` (Ollama, LM Studio, vLLM, ...)."""

    spec: EncoderSpec
    timeout_seconds: float = 120.0

    def _embed(self, inputs: list[str]) -> list[list[float]]:
        base = (self.spec.base_url or "http://127.0.0.1:11434/v1").rstrip("/")
        headers = {"Authorization": f"Bearer {self.spec.api_key or 'not-needed'}"}
        resp = httpx.post(
            f"{base}/embeddings",
            json={"model": self.spec.model, "input": inputs},
            headers=headers,
            timeout=self.timeout_seconds,
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"OpenAI-compatible embed HTTP {resp.status_code} from {base}/embeddings: {resp.text[:500]}")
        data = resp.json().get("data", [])
        ordered = sorted(data, key=lambda item: item.get("index", 0))
        embeddings = [item["embedding"] for item in ordered]
        if len(embeddings) != len(inputs):
            raise RuntimeError(f"OpenAI-compatible embed returned {len(embeddings)} vectors for {len(inputs)} inputs")
        return embeddings

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return self._embed([f"{self.spec.document_prefix}{text}" for text in texts])

    def embed_query(self, text: str) -> list[float]:
        return self._embed([f"{self.spec.query_prefix}{text}"])[0]


@dataclass(slots=True)
class TEIEncoder:
    """HuggingFace text-embeddings-inference / Infinity ``POST /embed``."""

    spec: EncoderSpec
    timeout_seconds: float = 120.0

    def _embed(self, inputs: list[str]) -> list[list[float]]:
        base = (self.spec.base_url or "http://127.0.0.1:8080").rstrip("/")
        resp = httpx.post(f"{base}/embed", json={"inputs": inputs}, timeout=self.timeout_seconds)
        resp.raise_for_status()
        return resp.json()

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return self._embed([f"{self.spec.document_prefix}{text}" for text in texts])

    def embed_query(self, text: str) -> list[float]:
        return self._embed([f"{self.spec.query_prefix}{text}"])[0]


@dataclass(slots=True)
class SentenceTransformerEncoder:
    """In-process encoder. Lazily imports sentence-transformers (pulls torch)."""

    spec: EncoderSpec
    _model: Any = field(default=None, init=False, repr=False)

    def _ensure(self) -> Any:
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.spec.model, device="cuda")
        return self._model

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        model = self._ensure()
        prefixed = [f"{self.spec.document_prefix}{t}" for t in texts]
        return model.encode(prefixed, normalize_embeddings=self.spec.normalize).tolist()

    def embed_query(self, text: str) -> list[float]:
        model = self._ensure()
        vec = model.encode([f"{self.spec.query_prefix}{text}"], normalize_embeddings=self.spec.normalize)
        return vec[0].tolist()


def build_encoder(spec: EncoderSpec) -> Encoder:
    match spec.backend:
        case "openai":
            return OpenAIEncoder(spec)
        case "ollama":
            return OllamaEncoder(spec)
        case "tei":
            return TEIEncoder(spec)
        case "sentence-transformers":
            return SentenceTransformerEncoder(spec)
        case other:
            raise ValueError(f"Unknown encoder backend: {other!r}")


# --------------------------------------------------------------------------- #
# Rerankers
# --------------------------------------------------------------------------- #
class Reranker(Protocol):
    def rerank(self, query: str, candidates: Sequence[Candidate], top_k: int) -> list[Candidate]: ...


@dataclass(slots=True)
class NoOpReranker:
    """Keeps the vector-search order; used as the bake-off baseline."""

    def rerank(self, query: str, candidates: Sequence[Candidate], top_k: int) -> list[Candidate]:
        return _renumber(list(candidates)[:top_k])


@dataclass(slots=True)
class TEIReranker:
    spec: RerankerSpec
    timeout_seconds: float = 120.0

    def rerank(self, query: str, candidates: Sequence[Candidate], top_k: int) -> list[Candidate]:
        if not candidates:
            return []
        base = (self.spec.base_url or "http://127.0.0.1:8081").rstrip("/")
        resp = httpx.post(
            f"{base}/rerank",
            json={"query": query, "texts": [c.text for c in candidates]},
            timeout=self.timeout_seconds,
        )
        resp.raise_for_status()
        scored = resp.json()  # [{"index": int, "score": float}, ...]
        ordered: list[Candidate] = []
        for item in scored:
            cand = candidates[int(item["index"])]
            cand.score = float(item["score"])
            ordered.append(cand)
        ordered.sort(key=lambda c: (c.score if c.score is not None else 0.0), reverse=True)
        return _renumber(ordered[:top_k])


@dataclass(slots=True)
class CrossEncoderReranker:
    """In-process cross-encoder. Lazily imports sentence-transformers (pulls torch)."""

    spec: RerankerSpec
    _model: Any = field(default=None, init=False, repr=False)

    def _ensure(self) -> Any:
        if self._model is None:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self.spec.model, device="cuda")
        return self._model

    def rerank(self, query: str, candidates: Sequence[Candidate], top_k: int) -> list[Candidate]:
        if not candidates:
            return []
        model = self._ensure()
        scores = model.predict([(query, c.text) for c in candidates])
        for cand, score in zip(candidates, scores, strict=True):
            cand.score = float(score)
        ordered = sorted(candidates, key=lambda c: (c.score if c.score is not None else 0.0), reverse=True)
        return _renumber(list(ordered)[:top_k])


def build_reranker(spec: RerankerSpec) -> Reranker:
    match spec.backend:
        case "none":
            return NoOpReranker()
        case "tei":
            return TEIReranker(spec)
        case "sentence-transformers":
            return CrossEncoderReranker(spec)
        case other:
            raise ValueError(f"Unknown reranker backend: {other!r}")


def _renumber(candidates: list[Candidate]) -> list[Candidate]:
    for rank, cand in enumerate(candidates, start=1):
        cand.rank = rank
    return candidates


# --------------------------------------------------------------------------- #
# Retriever
# --------------------------------------------------------------------------- #
@dataclass(slots=True)
class Retriever:
    """Ties an encoder + a Chroma collection + a reranker into one ``search``."""

    config: RetrievalConfig
    collection: Any  # chromadb Collection
    encoder: Encoder
    reranker: Reranker

    @classmethod
    def from_config(cls, config: RetrievalConfig, collection: Any) -> "Retriever":
        return cls(
            config=config,
            collection=collection,
            encoder=build_encoder(config.encoder),
            reranker=build_reranker(config.reranker),
        )

    def search(self, query: str, *, fetch_k: int | None = None, top_k: int | None = None) -> list[Candidate]:
        fetch_k = fetch_k or self.config.fetch_k
        top_k = top_k or self.config.top_k
        query_embedding = self.encoder.embed_query(query)
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=fetch_k,
            include=["documents", "metadatas", "distances"],
        )
        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        candidates = [
            Candidate(chunk_id=str(cid), text=str(text), metadata=dict(meta or {}), distance=float(dist))
            for cid, text, meta, dist in zip(ids, documents, metadatas, distances, strict=True)
        ]
        if not candidates:
            return []
        return self.reranker.rerank(query, candidates, top_k)
