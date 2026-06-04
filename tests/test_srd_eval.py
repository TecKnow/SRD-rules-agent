import argparse
import os
from pathlib import Path

from srd_eval.config import load_env
from srd_eval import gather_rag
from srd_eval.gather_no_rag import SYSTEM_PROMPT, completed_pairs, existing_run_id, make_user_prompt
from srd_eval.grade_deepeval import default_output_path, expected_output
from srd_eval.io import append_jsonl, read_jsonl, write_jsonl


def test_read_jsonl_accepts_utf8_bom(tmp_path: Path) -> None:
    path = tmp_path / "rows.jsonl"
    path.write_text('\ufeff{"id": "first"}\n{"id": "second"}\n', encoding="utf-8")

    assert [row["id"] for row in read_jsonl(path)] == ["first", "second"]


def test_write_jsonl_round_trips(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "rows.jsonl"

    count = write_jsonl(path, [{"id": "a", "value": 1}, {"id": "b", "value": 2}])

    assert count == 2
    assert list(read_jsonl(path)) == [{"id": "a", "value": 1}, {"id": "b", "value": 2}]


def test_append_jsonl_round_trips(tmp_path: Path) -> None:
    path = tmp_path / "answers.jsonl"

    append_jsonl(path, {"id": "first"})
    append_jsonl(path, {"id": "second"})

    assert list(read_jsonl(path)) == [{"id": "first"}, {"id": "second"}]


def test_expected_output_prefers_refined_gold_fields() -> None:
    row = {
        "expected_answer": "Original answer",
        "rubric": "Original rubric",
        "ai_refined_expected_answer": "Refined answer",
        "ai_refined_rubric": "Refined rubric",
    }

    output = expected_output(row)

    assert "Refined answer" in output
    assert "Refined rubric" in output
    assert "Original answer" not in output
    assert "Original rubric" not in output


def test_default_output_path_sits_next_to_answers() -> None:
    assert default_output_path(Path("runs/no_rag/run/answers.jsonl")) == Path(
        "runs/no_rag/run/answers.deepeval_scores.jsonl"
    )


def test_load_env_reads_file_without_overriding_shell_values(tmp_path: Path, monkeypatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "OPENROUTER_API_KEY=from-file\nDEEPEVAL_JUDGE_MODEL=from-file\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("DEEPEVAL_JUDGE_MODEL", "from-shell")

    load_env(env_file)

    assert os.environ["OPENROUTER_API_KEY"] == "from-file"
    assert os.environ["DEEPEVAL_JUDGE_MODEL"] == "from-shell"


def test_answer_prompt_does_not_leak_benchmark_metadata() -> None:
    row = {
        "question": "How does Surprise work in SRD 5.2.1?",
        "category": "version-specific",
        "difficulty": "easy",
        "answer_status": "resolved",
        "contentiousness": "low",
    }

    prompt = make_user_prompt(row)

    assert "How does Surprise work" in prompt
    assert "version-specific" not in prompt
    assert "difficulty" not in prompt
    assert "answer_status" not in prompt
    assert "no-RAG" not in prompt


def test_system_prompt_does_not_name_the_pipeline() -> None:
    assert "no-RAG" not in SYSTEM_PROMPT
    assert "no_rag" not in SYSTEM_PROMPT


def test_system_prompt_discourages_stale_rules_and_invented_citations() -> None:
    assert "older 2014 D&D rules" in SYSTEM_PROMPT
    assert "prefer SRD 5.2.1" in SYSTEM_PROMPT
    assert "Do not cite page numbers" in SYSTEM_PROMPT
    assert "provided in the question" in SYSTEM_PROMPT
    assert "explain the rule without citations" in SYSTEM_PROMPT


def test_resume_helpers_find_successful_completed_pairs(tmp_path: Path) -> None:
    path = tmp_path / "answers.jsonl"
    append_jsonl(path, {"run_id": "run-1", "question_id": "q1", "model": "m1", "answer": "ok"})
    append_jsonl(path, {"run_id": "run-1", "question_id": "q2", "model": "m1", "answer": "", "error": "failed"})

    assert existing_run_id(path) == "run-1"
    assert completed_pairs(path) == {("q1", "m1")}


def test_rag_prompt_includes_context_without_metadata_leak() -> None:
    row = {
        "id": "q1",
        "question": "Can True Strike be used with Extra Attack?",
        "category": "complex",
        "difficulty": "medium",
    }
    context = [
        {
            "rank": 1,
            "chunk_id": "spells.md::true-strike",
            "distance": 0.1,
            "metadata": {"source_file": "spells.md", "name": "True Strike"},
            "text": "True Strike has special casting and attack text.",
        }
    ]

    prompt = gather_rag.make_user_prompt(row, context)

    assert "Can True Strike" in prompt
    assert "True Strike has special" in prompt
    assert "spells.md | True Strike" in prompt
    assert "complex" not in prompt
    assert "difficulty" not in prompt


def test_rag_answer_record_includes_retrieval_evidence() -> None:
    args = argparse.Namespace(
        embedding_model="fake-embedding",
        embeddings=Path("embeddings.jsonl"),
        chroma_dir=Path("chroma"),
        collection_name="collection",
        top_k=6,
    )
    row = {"id": "q1", "question": "Question?", "category": "common"}
    context = [{"rank": 1, "chunk_id": "chunk", "distance": 0.2, "metadata": {}, "text": "Rule text"}]

    record = gather_rag.make_answer_record(
        run_id="run",
        row=row,
        model="model",
        retrieved_context=context,
        result={"text": "Answer", "raw_response": {"ok": True}},
        args=args,
    )

    assert record["pipeline"] == "rag_chroma"
    assert record["answer"] == "Answer"
    assert record["rag"]["top_k"] == 6
    assert record["rag"]["retrieved_context"] == context
