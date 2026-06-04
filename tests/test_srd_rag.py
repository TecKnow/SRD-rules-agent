import argparse
from pathlib import Path

import pytest

from srd_eval.io import append_jsonl, read_jsonl
from srd_rag.embed_srd import (
    ChunkConfig,
    OpenRouterEmbeddingsClient,
    chunk_corpus,
    completed_embedding_ids,
    embed_chunks,
    markdown_files,
    run,
)


class FakeEmbeddingsClient:
    def __init__(self, *, dimensions: int = 3, fail: bool = False) -> None:
        self.dimensions = dimensions
        self.fail = fail
        self.calls: list[list[str]] = []

    def embed_texts(self, *, model: str, texts: list[str]) -> list[list[float]]:
        if self.fail:
            raise RuntimeError("fake failure")
        self.calls.append(list(texts))
        return [[float(index + offset) for offset in range(self.dimensions)] for index, _ in enumerate(texts)]


def write_markdown(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_markdown_files_excludes_repository_docs(tmp_path: Path) -> None:
    write_markdown(tmp_path / "README.md", "# Ignore me")
    write_markdown(tmp_path / "spells.md", "# Spells")
    write_markdown(tmp_path / "CHANGELOG.md", "# Ignore me too")

    assert [path.name for path in markdown_files(tmp_path)] == ["spells.md"]


def test_chunk_corpus_preserves_header_metadata_and_stable_ids(tmp_path: Path) -> None:
    write_markdown(
        tmp_path / "spells.md",
        """# Spells
## Level 2 Spells
### Spike Growth
The ground sprouts hard spikes and thorns.
""",
    )

    config = ChunkConfig(source_dir=tmp_path, chunk_size=1200, chunk_overlap=100)
    first = chunk_corpus(config)
    second = chunk_corpus(config)

    assert [chunk["id"] for chunk in first] == [chunk["id"] for chunk in second]
    assert len(first) == 1
    metadata = first[0]["metadata"]
    assert metadata["h1"] == "Spells"
    assert metadata["h2"] == "Level 2 Spells"
    assert metadata["h3"] == "Spike Growth"
    assert metadata["source_file"] == "spells.md"
    assert metadata["srd_version"] == "5.2.1"
    assert metadata["entity_type"] == "spell"
    assert metadata["chunk_id"] == first[0]["id"]


def test_chunk_corpus_recursively_splits_oversized_sections(tmp_path: Path) -> None:
    long_text = " ".join(f"word{index}" for index in range(600))
    write_markdown(tmp_path / "rules-glossary.md", f"# Rules Glossary\n## Huge Rule\n{long_text}\n")

    chunks = chunk_corpus(ChunkConfig(source_dir=tmp_path, chunk_size=80, chunk_overlap=10))

    assert len(chunks) > 1
    assert all(chunk["metadata"]["source_file"] == "rules-glossary.md" for chunk in chunks)
    assert all(len(chunk["text"]) < len(long_text) for chunk in chunks)


def test_completed_embedding_ids_counts_only_successful_rows(tmp_path: Path) -> None:
    path = tmp_path / "embeddings.jsonl"
    append_jsonl(path, {"id": "ok", "embedding": [1.0], "error": ""})
    append_jsonl(path, {"id": "failed", "embedding": [], "error": "nope"})

    assert completed_embedding_ids(path) == {"ok"}


def test_embed_chunks_resumes_and_writes_valid_jsonl(tmp_path: Path) -> None:
    output = tmp_path / "embeddings.jsonl"
    chunks = [
        {"id": "already-done", "text": "Done", "metadata": {"source_file": "a.md"}},
        {"id": "new", "text": "New", "metadata": {"source_file": "a.md"}},
    ]
    append_jsonl(output, {"id": "already-done", "embedding": [9.0], "error": ""})

    written, skipped = embed_chunks(
        chunks=chunks,
        output_path=output,
        model="fake-model",
        client=FakeEmbeddingsClient(),
        resume=True,
        workers=1,
        batch_size=1,
        retries=0,
        retry_delay_seconds=0.0,
        continue_on_error=False,
    )

    rows = list(read_jsonl(output))
    assert written == 1
    assert skipped == 1
    assert [row["id"] for row in rows] == ["already-done", "new"]
    assert rows[-1]["embedding_dimensions"] == 3


def test_embed_chunks_records_errors_only_when_requested(tmp_path: Path) -> None:
    output = tmp_path / "embeddings.jsonl"
    chunks = [{"id": "bad", "text": "Bad", "metadata": {"source_file": "a.md"}}]

    written, skipped = embed_chunks(
        chunks=chunks,
        output_path=output,
        model="fake-model",
        client=FakeEmbeddingsClient(fail=True),
        resume=False,
        workers=1,
        batch_size=1,
        retries=0,
        retry_delay_seconds=0.0,
        continue_on_error=True,
    )

    rows = list(read_jsonl(output))
    assert written == 1
    assert skipped == 0
    assert rows[0]["id"] == "bad"
    assert rows[0]["embedding"] == []
    assert "fake failure" in rows[0]["error"]


def test_embed_chunks_stops_on_error_without_continue(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="Embedding failed"):
        embed_chunks(
            chunks=[{"id": "bad", "text": "Bad", "metadata": {"source_file": "a.md"}}],
            output_path=tmp_path / "embeddings.jsonl",
            model="fake-model",
            client=FakeEmbeddingsClient(fail=True),
            resume=False,
            workers=1,
            batch_size=1,
            retries=0,
            retry_delay_seconds=0.0,
            continue_on_error=False,
        )


def test_dry_run_and_chunks_only_do_not_require_openrouter_key(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    write_markdown(tmp_path / "spells.md", "# Spells\n## Cantrips\n### Light\nA light spell.\n")

    dry_summary = run(
        argparse.Namespace(
            source_dir=tmp_path,
            runs_dir=tmp_path / "runs",
            run_id="run",
            output_dir=None,
            chunks_output=None,
            embeddings_output=None,
            model="fake-model",
            chunk_size=1200,
            chunk_overlap=100,
            batch_size=1,
            workers=1,
            limit=None,
            timeout_seconds=1,
            retries=0,
            retry_delay_seconds=0.0,
            resume=False,
            continue_on_error=False,
            dry_run=True,
            chunks_only=False,
        )
    )

    chunks_summary = run(
        argparse.Namespace(
            source_dir=tmp_path,
            runs_dir=tmp_path / "runs",
            run_id="run",
            output_dir=None,
            chunks_output=None,
            embeddings_output=None,
            model="fake-model",
            chunk_size=1200,
            chunk_overlap=100,
            batch_size=1,
            workers=1,
            limit=None,
            timeout_seconds=1,
            retries=0,
            retry_delay_seconds=0.0,
            resume=False,
            continue_on_error=False,
            dry_run=False,
            chunks_only=True,
        )
    )

    assert dry_summary["mode"] == "dry-run"
    assert chunks_summary["mode"] == "chunks-only"
    assert Path(chunks_summary["chunks_output"]).exists()


def test_embedding_client_requires_key(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "")

    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
        OpenRouterEmbeddingsClient(api_key=None)
