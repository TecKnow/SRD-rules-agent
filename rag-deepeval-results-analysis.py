# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "marimo[recommended]>=0.23.8",
#     "matplotlib==3.10.9",
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
    import matplotlib.pyplot as plt
    import pandas as pd
    from dotenv import load_dotenv

    from srd_eval.grade_deepeval import FAILURE_TYPES
    from srd_eval.io import read_jsonl

    return FAILURE_TYPES, Path, json, load_dotenv, mo, pd, plt, read_jsonl


@app.cell
def _(mo):
    mo.md("""
    # RAG DeepEval results analysis

    This notebook analyzes the RAG-assisted structured-judging results, summarizes
    failure types overall and by answer model, and lets you browse each model
    answer alongside the judge result and retrieved SRD context.
    """)
    return


@app.cell
def _(Path):
    NOTEBOOK_DIR = Path(__file__).parent
    RUN_DIR = NOTEBOOK_DIR / "runs" / "rag" / "rag-chroma-20260604-full"
    DEFAULT_SCORES_PATH = RUN_DIR / "answers.deepeval_scores.jsonl"
    DEFAULT_ANSWERS_PATH = RUN_DIR / "answers.jsonl"
    ENV_PATH = NOTEBOOK_DIR / ".env"
    return DEFAULT_ANSWERS_PATH, DEFAULT_SCORES_PATH, ENV_PATH


@app.cell
def _(ENV_PATH, load_dotenv, mo):
    load_dotenv(ENV_PATH, override=False)
    is_script_mode = mo.app_meta().mode == "script"
    return


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
    return answer_records_raw, score_records_raw


@app.cell
def _(FAILURE_TYPES, answer_records_raw, score_records_raw):
    def record_key(row):
        return (str(row.get("run_id")), str(row.get("question_id")), str(row.get("model")))

    def sorted_contexts(row):
        rag = row.get("rag", {})
        contexts = rag.get("retrieved_context", [])
        return sorted(contexts, key=lambda item: int(item.get("rank", 10**9)))

    answers_by_key = {record_key(row): row for row in answer_records_raw}
    score_error_records = [row for row in score_records_raw if row.get("error")]
    scored_records = [row for row in score_records_raw if not row.get("error") and "score" in row]
    merged_records = []

    for score_row in sorted(scored_records, key=lambda row: int(row.get("answer_index", 10**9))):
        answer_row = answers_by_key.get(record_key(score_row), {})
        failure_types = score_row.get("failure_types", {})
        failure_notes = score_row.get("failure_notes", {})
        _metadata = score_row.get("question_metadata") or answer_row.get("benchmark_metadata", {})
        rag = answer_row.get("rag", {})
        _retrieved_context = sorted_contexts(answer_row)
        distances = [
            float(context["distance"])
            for context in _retrieved_context
            if context.get("distance") is not None
        ]
        top_context = _retrieved_context[0] if _retrieved_context else {}
        top_metadata = top_context.get("metadata", {})
        active_failure_types = [failure_type for failure_type in FAILURE_TYPES if failure_types.get(failure_type)]
        merged_records.append(
            {
                **score_row,
                "question": answer_row.get("question", ""),
                "answer": answer_row.get("answer", ""),
                "prompt_version": answer_row.get("prompt_version", ""),
                "generated_at": answer_row.get("generated_at", ""),
                "rag": rag,
                "retrieved_context": _retrieved_context,
                "retrieved_context_count": len(_retrieved_context),
                "top_distance": distances[0] if distances else None,
                "avg_distance": sum(distances) / len(distances) if distances else None,
                "top_chunk_id": top_context.get("chunk_id", ""),
                "top_source_file": top_metadata.get("source_file", ""),
                "top_source_name": top_metadata.get("name", ""),
                "top_entity_type": top_metadata.get("entity_type", ""),
                "embedding_model": rag.get("embedding_model", ""),
                "collection_name": rag.get("collection_name", ""),
                "active_failure_types": active_failure_types,
                "active_failure_types_text": ", ".join(active_failure_types),
                "failure_count": len(active_failure_types),
                "category": _metadata.get("category", ""),
                "difficulty": _metadata.get("difficulty", ""),
                "answer_status": _metadata.get("answer_status", ""),
                "contentiousness": _metadata.get("contentiousness", ""),
                "verification_status": _metadata.get("verification_status", ""),
                "failure_notes_compact": {
                    failure_type: failure_notes.get(failure_type, "")
                    for failure_type in active_failure_types
                    if failure_notes.get(failure_type)
                },
            }
        )
    return merged_records, score_error_records


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
                "top_distance": row["top_distance"],
                "avg_distance": row["avg_distance"],
                "retrieved_context_count": row["retrieved_context_count"],
                "top_source_file": row["top_source_file"],
                "top_source_name": row["top_source_name"],
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
def _(merged_records, mo, results_df, score_error_records):
    total_rows = len(results_df)
    passed_rows = int(results_df["passed"].sum())
    failed_rows = total_rows - passed_rows
    flagged_rows = sum(1 for row in merged_records if row["failure_count"] > 0)
    average_score = results_df["score"].mean()
    average_top_distance = results_df["top_distance"].dropna().mean()
    mo.md(f"""
    **Rows analyzed:** {total_rows}

    **Passed:** {passed_rows} &nbsp;&nbsp; **Failed:** {failed_rows}

    **Rows with at least one failure flag:** {flagged_rows}

    **Average score:** {average_score:.3f}

    **Average top retrieval distance:** {average_top_distance:.3f}

    **Score error rows skipped:** {len(score_error_records)}
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
def _(error_counts_df, plt):
    failure_counts_plot_df = error_counts_df.sort_values("count", ascending=True)
    failure_counts_fig, failure_counts_ax = plt.subplots(figsize=(9, 4.8))
    failure_counts_ax.barh(
        failure_counts_plot_df["failure_type"],
        failure_counts_plot_df["count"],
        color="#3b6ea8",
    )
    failure_counts_ax.set_title("Failure Type Counts")
    failure_counts_ax.set_xlabel("Rows flagged")
    failure_counts_ax.set_ylabel("")
    failure_counts_ax.grid(axis="x", alpha=0.25)
    failure_counts_fig.tight_layout()
    failure_counts_fig
    return


@app.cell
def _(FAILURE_TYPES, merged_records, pd):
    model_rows = []
    for model in sorted({row["model"] for row in merged_records}):
        model_records = [row for row in merged_records if row["model"] == model]
        top_distances = [row["top_distance"] for row in model_records if row["top_distance"] is not None]
        base = {
            "model": model,
            "rows": len(model_records),
            "passed": sum(1 for row in model_records if row["passed"]),
            "failed": sum(1 for row in model_records if not row["passed"]),
            "avg_score": round(sum(float(row["score"]) for row in model_records) / len(model_records), 3),
            "flagged_rows": sum(1 for row in model_records if row["failure_count"] > 0),
            "avg_top_distance": round(sum(top_distances) / len(top_distances), 3) if top_distances else None,
        }
        for failure_type in FAILURE_TYPES:
            base[failure_type] = sum(1 for row in model_records if row["failure_types"].get(failure_type))
        model_rows.append(base)
    model_failure_df = pd.DataFrame(model_rows)
    model_failure_df
    return (model_failure_df,)


@app.cell
def _(FAILURE_TYPES, model_failure_df, plt):
    heatmap_data = model_failure_df.set_index("model")[list(FAILURE_TYPES)]
    heatmap_fig, heatmap_ax = plt.subplots(figsize=(11, 4.8))
    heatmap_image = heatmap_ax.imshow(heatmap_data.values, aspect="auto", cmap="YlOrRd")
    heatmap_ax.set_title("Failure Types by Answer Model")
    heatmap_ax.set_xticks(range(len(heatmap_data.columns)))
    heatmap_ax.set_xticklabels(heatmap_data.columns, rotation=45, ha="right")
    heatmap_ax.set_yticks(range(len(heatmap_data.index)))
    heatmap_ax.set_yticklabels(heatmap_data.index)
    for heatmap_row_index, heatmap_model_name in enumerate(heatmap_data.index):
        for heatmap_column_index, heatmap_failure_type in enumerate(heatmap_data.columns):
            heatmap_value = int(heatmap_data.loc[heatmap_model_name, heatmap_failure_type])
            heatmap_ax.text(
                heatmap_column_index,
                heatmap_row_index,
                str(heatmap_value),
                ha="center",
                va="center",
                fontsize=8,
            )
    heatmap_fig.colorbar(heatmap_image, ax=heatmap_ax, label="Rows flagged")
    heatmap_fig.tight_layout()
    heatmap_fig
    return


@app.cell
def _(merged_records, pd):
    context_rows = []
    for _merged_row in merged_records:
        for context in _merged_row["retrieved_context"]:
            context_metadata = context.get("metadata", {})
            context_rows.append(
                {
                    "question_id": _merged_row["question_id"],
                    "model": _merged_row["model"],
                    "score": _merged_row["score"],
                    "passed": _merged_row["passed"],
                    "rank": context.get("rank"),
                    "distance": context.get("distance"),
                    "source_file": context_metadata.get("source_file", ""),
                    "entity_type": context_metadata.get("entity_type", ""),
                    "name": context_metadata.get("name", ""),
                    "chunk_id": context.get("chunk_id", ""),
                }
            )
    contexts_df = pd.DataFrame(context_rows)
    return (contexts_df,)


@app.cell
def _(contexts_df):
    source_summary_df = (
        contexts_df.groupby(["source_file", "entity_type"], dropna=False)
        .agg(
            retrievals=("chunk_id", "count"),
            unique_chunks=("chunk_id", "nunique"),
            avg_rank=("rank", "mean"),
            avg_distance=("distance", "mean"),
        )
        .reset_index()
        .sort_values(["retrievals", "source_file", "entity_type"], ascending=[False, True, True])
    )
    source_summary_df["avg_rank"] = source_summary_df["avg_rank"].round(2)
    source_summary_df["avg_distance"] = source_summary_df["avg_distance"].round(3)
    source_summary_df
    return


@app.cell
def _(contexts_df, plt):
    top_source_counts_df = contexts_df["source_file"].value_counts().head(15).sort_values()
    source_counts_fig, source_counts_ax = plt.subplots(figsize=(9, 5.4))
    source_counts_ax.barh(top_source_counts_df.index, top_source_counts_df.values, color="#4f7d57")
    source_counts_ax.set_title("Most Retrieved Source Files")
    source_counts_ax.set_xlabel("Retrieved chunks")
    source_counts_ax.set_ylabel("")
    source_counts_ax.grid(axis="x", alpha=0.25)
    source_counts_fig.tight_layout()
    source_counts_fig
    return


@app.cell
def _(FAILURE_TYPES, merged_records, mo):
    model_options = ["All models"] + sorted({row["model"] for row in merged_records})
    failure_type_options = ["Any failure type", "No failure flags"] + list(FAILURE_TYPES)
    pass_options = ["All results", "Passed only", "Failed only"]
    source_file_options = ["Any source file"] + sorted(
        {
            context.get("metadata", {}).get("source_file", "")
            for row in merged_records
            for context in row["retrieved_context"]
            if context.get("metadata", {}).get("source_file")
        }
    )

    model_dropdown = mo.ui.dropdown(options=model_options, value="All models", label="Answer model")
    failure_type_dropdown = mo.ui.dropdown(
        options=failure_type_options,
        value="Any failure type",
        label="Failure type",
    )
    pass_dropdown = mo.ui.dropdown(options=pass_options, value="All results", label="Pass status")
    source_file_dropdown = mo.ui.dropdown(
        options=source_file_options,
        value="Any source file",
        label="Retrieved source file",
    )
    question_filter_input = mo.ui.text(value="", label="Question ID contains", full_width=True)
    mo.vstack(
        [
            mo.hstack([model_dropdown, failure_type_dropdown, pass_dropdown]),
            source_file_dropdown,
            question_filter_input,
        ]
    )
    return (
        failure_type_dropdown,
        model_dropdown,
        pass_dropdown,
        question_filter_input,
        source_file_dropdown,
    )


@app.cell
def _(
    failure_type_dropdown,
    merged_records,
    model_dropdown,
    pass_dropdown,
    question_filter_input,
    source_file_dropdown,
):
    question_filter = question_filter_input.value.strip().lower()
    filtered_records = []
    for _candidate_row in merged_records:
        if model_dropdown.value != "All models" and _candidate_row["model"] != model_dropdown.value:
            continue
        if pass_dropdown.value == "Passed only" and not _candidate_row["passed"]:
            continue
        if pass_dropdown.value == "Failed only" and _candidate_row["passed"]:
            continue
        if question_filter and question_filter not in _candidate_row["question_id"].lower():
            continue
        if failure_type_dropdown.value == "Any failure type" and _candidate_row["failure_count"] == 0:
            continue
        if failure_type_dropdown.value == "No failure flags" and _candidate_row["failure_count"] != 0:
            continue
        if failure_type_dropdown.value not in {"Any failure type", "No failure flags"}:
            if not _candidate_row["failure_types"].get(failure_type_dropdown.value):
                continue
        if source_file_dropdown.value != "Any source file":
            source_files = {
                context.get("metadata", {}).get("source_file", "")
                for context in _candidate_row["retrieved_context"]
            }
            if source_file_dropdown.value not in source_files:
                continue
        filtered_records.append(_candidate_row)
    return (filtered_records,)


@app.cell
def _(mo):
    page_size_dropdown = mo.ui.dropdown(
        options=["10", "25", "50", "100"],
        value="25",
        label="Rows per page",
    )
    page_number_input = mo.ui.text(value="1", label="Page number")
    mo.hstack([page_size_dropdown, page_number_input])
    return page_number_input, page_size_dropdown


@app.cell
def _(filtered_records, page_number_input, page_size_dropdown):
    page_size = int(page_size_dropdown.value)
    total_pages = max(1, (len(filtered_records) + page_size - 1) // page_size)
    page_text = page_number_input.value.strip()
    requested_page = int(page_text) if page_text.isdecimal() else 1
    page_number = min(max(1, requested_page), total_pages)
    start_offset = (page_number - 1) * page_size
    page_records = filtered_records[start_offset : start_offset + page_size]
    return page_number, page_records, start_offset, total_pages


@app.cell
def _(filtered_records, mo, page_number, total_pages):
    mo.md(f"""
    **Filtered rows:** {len(filtered_records)} &nbsp;&nbsp; **Page:** {page_number} of {total_pages}
    """)
    return


@app.cell
def _(page_records, pd, start_offset):
    page_df = pd.DataFrame(
        [
            {
                "row": start_offset + index,
                "question_id": row["question_id"],
                "model": row["model"],
                "score": row["score"],
                "passed": row["passed"],
                "failure_count": row["failure_count"],
                "active_failure_types": row["active_failure_types_text"],
                "top_source_file": row["top_source_file"],
                "top_distance": row["top_distance"],
            }
            for index, row in enumerate(page_records)
        ]
    )
    page_df
    return


@app.cell
def _(mo, page_records, start_offset):
    result_options = [
        (
            f"{start_offset + index}: {row['question_id']} | {row['model']} | "
            f"score={float(row['score']):.2f} | top={row['top_source_file'] or 'no source'} | "
            f"{row['active_failure_types_text'] or 'no flags'}"
        )
        for index, row in enumerate(page_records)
    ]
    result_options = result_options or ["No matching rows"]
    selected_result_dropdown = mo.ui.dropdown(
        options=result_options,
        value=result_options[0],
        label="Select result on this page",
        full_width=True,
    )
    selected_result_dropdown
    return result_options, selected_result_dropdown


@app.cell
def _(page_records, result_options, selected_result_dropdown):
    if page_records and selected_result_dropdown.value in result_options:
        selected_page_index = result_options.index(selected_result_dropdown.value)
        selected_record = page_records[selected_page_index]
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
                "top_source_file": selected_record.get("top_source_file", ""),
                "top_source_name": selected_record.get("top_source_name", ""),
                "top_distance": selected_record.get("top_distance", ""),
                "avg_distance": selected_record.get("avg_distance", ""),
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
def _(pd, selected_record):
    selected_context_df = pd.DataFrame(
        [
            {
                "rank": context.get("rank", ""),
                "distance": context.get("distance", ""),
                "source_file": context.get("metadata", {}).get("source_file", ""),
                "entity_type": context.get("metadata", {}).get("entity_type", ""),
                "name": context.get("metadata", {}).get("name", ""),
                "h1": context.get("metadata", {}).get("h1", ""),
                "h2": context.get("metadata", {}).get("h2", ""),
                "h3": context.get("metadata", {}).get("h3", ""),
                "h4": context.get("metadata", {}).get("h4", ""),
                "chunk_id": context.get("chunk_id", ""),
            }
            for context in selected_record.get("retrieved_context", [])
        ]
    )
    selected_context_df
    return


@app.cell
def _(mo, selected_record):
    context_options = [
        (
            f"{context.get('rank', '')}: "
            f"{context.get('metadata', {}).get('source_file', '')} | "
            f"{context.get('metadata', {}).get('name', '')} | "
            f"distance={float(context.get('distance', 0.0)):.3f}"
        )
        for context in selected_record.get("retrieved_context", [])
    ]
    context_options = context_options or ["No retrieved context"]
    selected_context_dropdown = mo.ui.dropdown(
        options=context_options,
        value=context_options[0],
        label="Select retrieved context",
        full_width=True,
    )
    selected_context_dropdown
    return context_options, selected_context_dropdown


@app.cell
def _(context_options, selected_context_dropdown, selected_record):
    _selected_retrieved_context = selected_record.get("retrieved_context", [])
    if _selected_retrieved_context and selected_context_dropdown.value in context_options:
        selected_context_index = context_options.index(selected_context_dropdown.value)
        selected_context = _selected_retrieved_context[selected_context_index]
    else:
        selected_context = {}
    return (selected_context,)


@app.cell
def _(json, mo, selected_context):
    selected_context_text = mo.ui.text_area(
        value=selected_context.get("text", ""),
        rows=12,
        label="Retrieved context text",
        disabled=True,
        full_width=True,
    )
    selected_context_metadata = mo.ui.text_area(
        value=json.dumps(selected_context.get("metadata", {}), ensure_ascii=False, indent=2, sort_keys=True),
        rows=8,
        label="Retrieved context metadata",
        disabled=True,
        full_width=True,
    )
    mo.vstack([selected_context_text, selected_context_metadata])
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
