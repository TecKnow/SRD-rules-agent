"""Central, env-overridable configuration for the SRD rules agent.

Distribution goal: one semi-technical person sets this up for their player group, with
**as few services as possible** and **no compute fees**. So the default is a single local
service -- Ollama's built-in OpenAI-compatible API (``/v1``) serving *both* the generation
LLM and the embedding model -- with the reranker optional and off by default. Generation
is an OpenAI-compatible backend, so the same app also points at LM Studio, vLLM, a shared
local server, or a hosted API by setting ``OPENAI_BASE_URL`` / ``OPENAI_API_KEY``.

The retrieval stack is described as *data* (``EncoderSpec`` / ``RerankerSpec`` /
``RetrievalConfig``) so the bake-off and the live agent share one code path and the index
signature can capture exactly which encoder + chunker produced a Chroma collection.

Nothing here imports torch / langchain / chromadb, so it is safe to import for read-only
checks. Heavy backends are constructed lazily in ``srd_agent.retrieval`` / ``srd_agent.agent``.
"""

import os
from dataclasses import dataclass, replace
from pathlib import Path

from srd_eval.config import load_env
from srd_eval.io import ROOT

# --- Paths -----------------------------------------------------------------
DEFAULT_SRD_SOURCE_DIR = ROOT / "data" / "source" / "downfallx-dnd-5e-srd-markdown"
AGENT_RUNS_DIR = ROOT / "runs" / "agent"
SRD_VERSION = "5.2.1"

# --- Default local endpoint (Ollama's OpenAI-compatible API) ---------------
# One service serves both chat and embeddings; no API key needed locally.
DEFAULT_OPENAI_BASE_URL = "http://127.0.0.1:11434/v1"
DEFAULT_OPENAI_API_KEY = "ollama"  # local servers ignore the value
DEFAULT_GEN_MODEL = "qwen2.5:7b-instruct"
DEFAULT_EMBED_MODEL = "nomic-embed-text"

# --- Optional reranker server (only if the bake-off picks one) -------------
DEFAULT_TEI_RERANK_URL = "http://127.0.0.1:8081"


@dataclass(frozen=True, slots=True)
class GenSpec:
    """How to generate answers / tool calls.

    ``backend='openai'`` (default) talks to any OpenAI-compatible ``/v1`` endpoint via
    ``ChatOpenAI`` -- maximally portable. ``backend='ollama'`` uses native ``ChatOllama``
    (exposes ``num_ctx`` / ``keep_alive``).
    """

    backend: str = "openai"
    model: str = DEFAULT_GEN_MODEL
    base_url: str = DEFAULT_OPENAI_BASE_URL
    api_key: str = DEFAULT_OPENAI_API_KEY
    temperature: float = 0.0
    num_ctx: int = 8192  # ollama backend only


@dataclass(frozen=True, slots=True)
class EncoderSpec:
    """How to turn text into vectors.

    ``backend`` is one of ``"openai"`` (OpenAI-compatible ``/v1/embeddings``),
    ``"ollama"`` (native ``/api/embed``), ``"tei"``, ``"sentence-transformers"``.
    ``query_prefix`` / ``document_prefix`` carry instruction prefixes some encoders need
    (e.g. nomic's ``search_query:`` / ``search_document:``).
    """

    backend: str
    model: str
    query_prefix: str = ""
    document_prefix: str = ""
    base_url: str | None = None
    api_key: str | None = None
    normalize: bool = True

    @property
    def id(self) -> str:
        """Stable identifier used in index signatures and run names."""
        return f"{self.backend}:{self.model}"


@dataclass(frozen=True, slots=True)
class RerankerSpec:
    """How to reorder candidate chunks. ``backend='none'`` disables reranking."""

    backend: str = "none"
    model: str = ""
    base_url: str | None = None

    @property
    def id(self) -> str:
        return "none" if self.backend == "none" else f"{self.backend}:{self.model}"


@dataclass(frozen=True, slots=True)
class RetrievalConfig:
    encoder: "EncoderSpec"
    reranker: RerankerSpec = RerankerSpec()
    fetch_k: int = 30  # candidates pulled from Chroma before reranking
    top_k: int = 6  # passages handed to the LLM after reranking
    chunk_size: int = 1200  # token budget per chunk (index-build param)
    chunk_overlap: int = 100

    @property
    def id(self) -> str:
        return (
            f"enc[{self.encoder.id}]_rr[{self.reranker.id}]"
            f"_cs{self.chunk_size}_co{self.chunk_overlap}_fk{self.fetch_k}_tk{self.top_k}"
        )


# --- Named building blocks the bake-off / CLI draw from --------------------
# nomic-embed-text REQUIRES task prefixes; no local server adds them automatically.
# Default: nomic over the same OpenAI-compatible endpoint as generation (one service).
NOMIC_OPENAI = EncoderSpec(
    backend="openai",
    model=DEFAULT_EMBED_MODEL,
    query_prefix="search_query: ",
    document_prefix="search_document: ",
    base_url=DEFAULT_OPENAI_BASE_URL,
    api_key=DEFAULT_OPENAI_API_KEY,
)
# Same model via Ollama's native embeddings API (alternate; different signature id).
NOMIC_OLLAMA = EncoderSpec(
    backend="ollama",
    model=DEFAULT_EMBED_MODEL,
    query_prefix="search_query: ",
    document_prefix="search_document: ",
)
# BGE-M3 served over TEI (no prefixes needed).
BGE_M3_TEI = EncoderSpec(backend="tei", model="BAAI/bge-m3")

NO_RERANK = RerankerSpec(backend="none")
BGE_RERANK_TEI = RerankerSpec(backend="tei", model="BAAI/bge-reranker-v2-m3")
MXBAI_RERANK_TEI = RerankerSpec(backend="tei", model="mixedbread-ai/mxbai-rerank-large-v2")


@dataclass(frozen=True, slots=True)
class AgentConfig:
    """Everything the live agent needs, resolved from the environment."""

    gen: GenSpec = GenSpec()
    retrieval: RetrievalConfig = RetrievalConfig(encoder=NOMIC_OPENAI, reranker=NO_RERANK)
    source_dir: Path = DEFAULT_SRD_SOURCE_DIR
    runs_dir: Path = AGENT_RUNS_DIR


def load_agent_config() -> AgentConfig:
    """Resolve the live agent configuration, applying ``.env`` and process env.

    Defaults to a single local Ollama service (OpenAI-compatible) for chat + embeddings
    with no reranker. Override the endpoint with ``OPENAI_BASE_URL`` / ``OPENAI_API_KEY``
    to point at LM Studio, vLLM, a shared local server, or a hosted API. Once the bake-off
    picks a reranker, set ``SRD_AGENT_RERANK_MODEL`` (+ ``SRD_AGENT_TEI_RERANK_URL``).
    """
    load_env()
    base_url = os.environ.get("OPENAI_BASE_URL") or os.environ.get(
        "SRD_AGENT_OPENAI_BASE_URL", DEFAULT_OPENAI_BASE_URL
    )
    # `or` (not a get-default) so an empty OPENAI_API_KEY in .env still falls back to the
    # local placeholder -- local servers ignore the value but the OpenAI client requires one.
    api_key = os.environ.get("OPENAI_API_KEY") or DEFAULT_OPENAI_API_KEY

    gen = GenSpec(
        backend=os.environ.get("SRD_AGENT_GEN_BACKEND", "openai"),
        model=os.environ.get("SRD_AGENT_GEN_MODEL", DEFAULT_GEN_MODEL),
        base_url=base_url,
        api_key=api_key,
        temperature=float(os.environ.get("SRD_AGENT_TEMPERATURE", "0.0")),
        num_ctx=int(os.environ.get("SRD_AGENT_NUM_CTX", "8192")),
    )

    embed_base = os.environ.get("SRD_AGENT_EMBED_BASE_URL", base_url)
    encoder = replace(NOMIC_OPENAI, base_url=embed_base, api_key=api_key)

    reranker = NO_RERANK
    rerank_model = os.environ.get("SRD_AGENT_RERANK_MODEL")
    if rerank_model:
        reranker = RerankerSpec(
            backend="tei",
            model=rerank_model,
            base_url=os.environ.get("SRD_AGENT_TEI_RERANK_URL", DEFAULT_TEI_RERANK_URL),
        )

    retrieval = RetrievalConfig(
        encoder=encoder,
        reranker=reranker,
        fetch_k=int(os.environ.get("SRD_AGENT_FETCH_K", "30")),
        top_k=int(os.environ.get("SRD_AGENT_TOP_K", "6")),
    )
    return AgentConfig(gen=gen, retrieval=retrieval)
