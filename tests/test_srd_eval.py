from pathlib import Path

from srd_eval.grade_deepeval import default_output_path, expected_output
from srd_eval.io import read_jsonl, write_jsonl


def test_read_jsonl_accepts_utf8_bom(tmp_path: Path) -> None:
    path = tmp_path / "rows.jsonl"
    path.write_text('\ufeff{"id": "first"}\n{"id": "second"}\n', encoding="utf-8")

    assert [row["id"] for row in read_jsonl(path)] == ["first", "second"]


def test_write_jsonl_round_trips(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "rows.jsonl"

    count = write_jsonl(path, [{"id": "a", "value": 1}, {"id": "b", "value": 2}])

    assert count == 2
    assert list(read_jsonl(path)) == [{"id": "a", "value": 1}, {"id": "b", "value": 2}]


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
