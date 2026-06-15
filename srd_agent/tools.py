"""Agent tools. v1 ships the core retrieval tool, ``search_srd``.

The tool returns a ``(content, artifact)`` pair: the formatted passage text is what
the LLM reads, and the structured ``artifact`` (the candidate chunks + metadata) rides
along on the ToolMessage so the FastAPI layer can surface citations without re-running
retrieval.
"""

from collections.abc import Sequence
from typing import Any

from langchain_core.tools import StructuredTool

from .retrieval import Candidate, Retriever


def source_label(metadata: dict[str, Any]) -> str:
    """e.g. ``rules-glossary.md | Grappling [Action]`` -- mirrors gather_rag's labels."""
    source_file = metadata.get("source_file", "unknown-source")
    name = metadata.get("name")
    if name and name != source_file:
        return f"{source_file} | {name}"
    return str(source_file)


def format_candidates(candidates: Sequence[Candidate]) -> str:
    if not candidates:
        return "No SRD passages matched the query."
    blocks = [f"[{c.rank}] {source_label(c.metadata)}\n{c.text}" for c in candidates]
    return "\n\n---\n\n".join(blocks)


def candidate_citation(candidate: Candidate) -> dict[str, Any]:
    return {
        "rank": candidate.rank,
        "chunk_id": candidate.chunk_id,
        "source": source_label(candidate.metadata),
        "source_file": candidate.metadata.get("source_file"),
        "name": candidate.metadata.get("name"),
        "distance": candidate.distance,
        "score": candidate.score,
    }


_SEARCH_DESCRIPTION = (
    "Search the official D&D SRD 5.2.1 rules text and return the most relevant passages. "
    "Call this before answering any rules question, and call it again with a refined query "
    "if the first passages are insufficient. Input is a natural-language search query."
)


def make_search_srd_tool(retriever: Retriever) -> StructuredTool:
    """Bind a ``search_srd`` tool to a specific retriever instance."""

    def search_srd(query: str) -> tuple[str, list[dict[str, Any]]]:
        candidates = retriever.search(query)
        return format_candidates(candidates), [candidate_citation(c) for c in candidates]

    return StructuredTool.from_function(
        func=search_srd,
        name="search_srd",
        description=_SEARCH_DESCRIPTION,
        response_format="content_and_artifact",
    )
