# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "marimo[recommended]>=0.23.8",
#     "pandas>=2.3.3",
#     "python-dotenv>=1.2.2",
# ]
# ///

import marimo

__generated_with = "0.23.8"
app = marimo.App(width="medium")


@app.cell
def _():
    import json
    from pathlib import Path

    import marimo as mo
    import pandas as pd
    from dotenv import load_dotenv

    from srd_eval.grade_deepeval import FAILURE_TYPES
    from srd_eval.io import read_jsonl

    return FAILURE_TYPES, Path, json, load_dotenv, mo, pd, read_jsonl


@app.cell
def _(mo):
    mo.md("""
    # DeepEval results analysis

    This notebook analyzes the cleaned structured-judging results, summarizes
    failure types overall and by answer model, and lets you browse individual
    model answers alongside the judge's score, rationale, and diagnostic flags.
    """)
    return


@app.cell
def _(Path):
    NOTEBOOK_DIR = Path(__file__).parent
    RUN_DIR = NOTEBOOK_DIR / "runs" / "no_rag" / "no-rag-20260603T074521Z-07aa8696"
    DEFAULT_SCORES_PATH = RUN_DIR / "answers_for_grading.deepeval_scores.success_only.jsonl"
    DEFAULT_ANSWERS_PATH = RUN_DIR / "answers_for_grading.jsonl"
    ENV_PATH = NOTEBOOK_DIR / ".env"
    return DEFAULT_ANSWERS_PATH, DEFAULT_SCORES_PATH, ENV_PATH


@app.cell
def _(ENV_PATH, load_dotenv, mo):
    load_dotenv(ENV_PATH, override=False)
    is_script_mode = mo.app_meta().mode == "script"
    return (is_script_mode,)


@app.cell
def _(DEFAULT_ANSWERS_PATH, DEFAULT_SCORES_PATH, mo):
    scores_path_input = mo.ui.text(
        value=str(DEFAULT_SCORES_PATH),
        label="Scores JSONL path",
        full_width=True,
    )
    answers_path_input = mo.ui.text(
        value=str(DEFAULT_ANSWERS_PATH),
        label="Answers JSONL path",
        full_width=True,
    )
    mo.vstack([scores_path_input, answers_path_input])
    return answers_path_input, scores_path_input


@app.cell
def _(Path, answers_path_input, read_jsonl, scores_path_input):
    scores_path = Path(scores_path_input.value)
    answers_path = Path(answers_path_input.value)
    score_records_raw = list(read_jsonl(scores_path))
    answer_records_raw = list(read_jsonl(answers_path))
    return answer_records_raw, answers_path, score_records_raw, scores_path


@app.cell
def _(FAILURE_TYPES, answer_records_raw, score_records_raw):
    def record_key(row):
        return (str(row.get("run_id")), str(row.get("question_id")), str(row.get("model")))

    answers_by_key = {record_key(row): row for row in answer_records_raw}
    merged_records = []
    for score_row in sorted(score_records_raw, key=lambda row: int(row.get("answer_index", 10**9))):
        answer_row = answers_by_key.get(record_key(score_row), {})
        failure_types = score_row.get("failure_types", {})
        failure_notes = score_row.get("failure_notes", {})
        metadata = score_row.get("question_metadata", {})
        active_failure_types = [failure_type for failure_type in FAILURE_TYPES if failure_types.get(failure_type)]
        merged_records.append(
            {
                **score_row,
                "question": answer_row.get("question", ""),
                "answer": answer_row.get("answer", ""),
                "prompt_version": answer_row.get("prompt_version", ""),
                "active_failure_types": active_failure_types,
                "active_failure_types_text": ", ".join(active_failure_types),
                "failure_count": len(active_failure_types),
                "category": metadata.get("category", ""),
                "difficulty": metadata.get("difficulty", ""),
                "answer_status": metadata.get("answer_status", ""),
                "contentiousness": metadata.get("contentiousness", ""),
                "verification_status": metadata.get("verification_status", ""),
                "failure_notes_compact": {
                    failure_type: failure_notes.get(failure_type, "")
                    for failure_type in active_failure_types
                    if failure_notes.get(failure_type)
                },
            }
        )
    return merged_records, record_key


@app.cell
def _(merged_records, pd):
    results_df = pd.DataFrame(
        [
            {
                "answer_index": row.get("answer_index"),
                "question_id": row["question_id"],
                "model": row["model"],
                "score": row["score"],
                "passed": row["passed"],
                "failure_count": row["failure_count"],
                "active_failure_types": row["active_failure_types_text"],
                "diagnostic_confidence": row["diagnostic_confidence"],
                "category": row["category"],
                "difficulty": row["difficulty"],
                "answer_status": row["answer_status"],
                "contentiousness": row["contentiousness"],
            }
            for row in merged_records
        ]
    )
    return (results_df,)


@app.cell
def _(merged_records, mo, results_df):
    total_rows = len(results_df)
    passed_rows = int(results_df["passed"].sum())
    failed_rows = total_rows - passed_rows
    flagged_rows = sum(1 for row in merged_records if row["failure_count"] > 0)
    average_score = results_df["score"].mean()
    mo.md(f"""
    **Rows analyzed:** {total_rows}

    **Passed:** {passed_rows} &nbsp;&nbsp; **Failed:** {failed_rows}

    **Rows with at least one failure flag:** {flagged_rows}

    **Average score:** {average_score:.3f}
    """)
    return


@app.cell
def _(FAILURE_TYPES, merged_records, pd):
    error_counts_df = pd.DataFrame(
        [
            {
                "failure_type": failure_type,
                "count": sum(1 for row in merged_records if row["failure_types"].get(failure_type)),
                "percent_of_rows": round(
                    100 * sum(1 for row in merged_records if row["failure_types"].get(failure_type)) / len(merged_records),
                    1,
                ),
            }
            for failure_type in FAILURE_TYPES
        ]
    ).sort_values(["count", "failure_type"], ascending=[False, True])
    error_counts_df
    return (error_counts_df,)


@app.cell
def _(FAILURE_TYPES, merged_records, pd):
    model_rows = []
    for model in sorted({row["model"] for row in merged_records}):
        model_records = [row for row in merged_records if row["model"] == model]
        base = {
            "model": model,
            "rows": len(model_records),
            "passed": sum(1 for row in model_records if row["passed"]),
            "failed": sum(1 for row in model_records if not row["passed"]),
            "avg_score": round(sum(float(row["score"]) for row in model_records) / len(model_records), 3),
            "flagged_rows": sum(1 for row in model_records if row["failure_count"] > 0),
        }
        for failure_type in FAILURE_TYPES:
            base[failure_type] = sum(1 for row in model_records if row["failure_types"].get(failure_type))
        model_rows.append(base)
    model_failure_df = pd.DataFrame(model_rows)
    model_failure_df
    return (model_failure_df,)


@app.cell
def _(FAILURE_TYPES, merged_records, mo):
    model_options = ["All models"] + sorted({row["model"] for row in merged_records})
    failure_type_options = ["Any failure type", "No failure flags"] + list(FAILURE_TYPES)
    pass_options = ["All results", "Passed only", "Failed only"]

    model_dropdown = mo.ui.dropdown(options=model_options, value="All models", label="Answer model")
    failure_type_dropdown = mo.ui.dropdown(
        options=failure_type_options,
        value="Any failure type",
        label="Failure type",
    )
    pass_dropdown = mo.ui.dropdown(options=pass_options, value="All results", label="Pass status")
    question_filter_input = mo.ui.text(value="", label="Question ID contains", full_width=True)
    mo.vstack(
        [
            mo.hstack([model_dropdown, failure_type_dropdown, pass_dropdown]),
            question_filter_input,
        ]
    )
    return failure_type_dropdown, model_dropdown, pass_dropdown, question_filter_input


@app.cell
def _(
    failure_type_dropdown,
    merged_records,
    model_dropdown,
    pass_dropdown,
    question_filter_input,
):
    question_filter = question_filter_input.value.strip().lower()
    filtered_records = []
    for row in merged_records:
        if model_dropdown.value != "All models" and row["model"] != model_dropdown.value:
            continue
        if pass_dropdown.value == "Passed only" and not row["passed"]:
            continue
        if pass_dropdown.value == "Failed only" and row["passed"]:
            continue
        if question_filter and question_filter not in row["question_id"].lower():
            continue
        if failure_type_dropdown.value == "Any failure type" and row["failure_count"] == 0:
            continue
        if failure_type_dropdown.value == "No failure flags" and row["failure_count"] != 0:
            continue
        if failure_type_dropdown.value not in {"Any failure type", "No failure flags"}:
            if not row["failure_types"].get(failure_type_dropdown.value):
                continue
        filtered_records.append(row)
    return (filtered_records,)


@app.cell
def _(filtered_records, mo):
    max_index = max(0, len(filtered_records) - 1)
    result_index_slider = mo.ui.slider(
        start=0,
        stop=max_index,
        value=0,
        label="Result index",
    )
    mo.vstack(
        [
            mo.md(f"**Filtered rows:** {len(filtered_records)}"),
            result_index_slider,
        ]
    )
    return (result_index_slider,)


@app.cell
def _(filtered_records, result_index_slider):
    if filtered_records:
        selected_record = filtered_records[min(result_index_slider.value, len(filtered_records) - 1)]
    else:
        selected_record = {}
    return (selected_record,)


@app.cell
def _(pd, selected_record):
    selected_summary_df = pd.DataFrame(
        [
            {
                "question_id": selected_record.get("question_id", ""),
                "model": selected_record.get("model", ""),
                "score": selected_record.get("score", ""),
                "passed": selected_record.get("passed", ""),
                "confidence": selected_record.get("diagnostic_confidence", ""),
                "active_failure_types": selected_record.get("active_failure_types_text", ""),
                "category": selected_record.get("category", ""),
                "difficulty": selected_record.get("difficulty", ""),
                "answer_status": selected_record.get("answer_status", ""),
            }
        ]
    )
    selected_summary_df
    return


@app.cell
def _(mo, selected_record):
    question_view = mo.md(f"""
    ### Question

    {selected_record.get("question", "")}
    """)
    answer_view = mo.md(f"""
    ### Model answer

    {selected_record.get("answer", "")}
    """)
    rationale_view = mo.md(f"""
    ### Judge rationale

    {selected_record.get("rationale", "")}
    """)
    mo.vstack([question_view, answer_view, rationale_view])
    return


@app.cell
def _(FAILURE_TYPES, pd, selected_record):
    selected_failure_df = pd.DataFrame(
        [
            {
                "failure_type": failure_type,
                "present": bool(selected_record.get("failure_types", {}).get(failure_type)),
                "note": selected_record.get("failure_notes", {}).get(failure_type, ""),
            }
            for failure_type in FAILURE_TYPES
        ]
    )
    selected_failure_df
    return


@app.cell
def _(json, mo, selected_record):
    selected_json_preview = mo.ui.text_area(
        value=json.dumps(selected_record, ensure_ascii=False, indent=2, sort_keys=True),
        rows=14,
        label="Selected merged record JSON",
        disabled=True,
        full_width=True,
    )
    selected_json_preview
    return


if __name__ == "__main__":
    app.run()
