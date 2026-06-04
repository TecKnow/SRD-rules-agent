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
    # RAG vs no-RAG DeepEval comparison

    Compare the judged no-RAG and RAG-assisted answer sets by shared question
    and answer model, then browse matched answer and judgement pairs side by side.
    """)
    return


@app.cell
def _(Path):
    NOTEBOOK_DIR = Path(__file__).parent
    NO_RAG_RUN_DIR = NOTEBOOK_DIR / "runs" / "no_rag" / "no-rag-20260603T074521Z-07aa8696"
    RAG_RUN_DIR = NOTEBOOK_DIR / "runs" / "rag" / "rag-chroma-20260604-full"

    DEFAULT_NO_RAG_SCORES_PATH = NO_RAG_RUN_DIR / "answers_for_grading.deepeval_scores.success_only.jsonl"
    DEFAULT_NO_RAG_ANSWERS_PATH = NO_RAG_RUN_DIR / "answers_for_grading.jsonl"
    DEFAULT_RAG_SCORES_PATH = RAG_RUN_DIR / "answers.deepeval_scores.jsonl"
    DEFAULT_RAG_ANSWERS_PATH = RAG_RUN_DIR / "answers.jsonl"
    ENV_PATH = NOTEBOOK_DIR / ".env"
    return (
        DEFAULT_NO_RAG_ANSWERS_PATH,
        DEFAULT_NO_RAG_SCORES_PATH,
        DEFAULT_RAG_ANSWERS_PATH,
        DEFAULT_RAG_SCORES_PATH,
        ENV_PATH,
    )


@app.cell
def _(ENV_PATH, load_dotenv, mo):
    load_dotenv(ENV_PATH, override=False)
    is_script_mode = mo.app_meta().mode == "script"
    return


@app.cell
def _(
    DEFAULT_NO_RAG_ANSWERS_PATH,
    DEFAULT_NO_RAG_SCORES_PATH,
    DEFAULT_RAG_ANSWERS_PATH,
    DEFAULT_RAG_SCORES_PATH,
    mo,
):
    no_rag_scores_path_input = mo.ui.text(
        value=str(DEFAULT_NO_RAG_SCORES_PATH),
        label="No-RAG scores JSONL path",
        full_width=True,
    )
    no_rag_answers_path_input = mo.ui.text(
        value=str(DEFAULT_NO_RAG_ANSWERS_PATH),
        label="No-RAG answers JSONL path",
        full_width=True,
    )
    rag_scores_path_input = mo.ui.text(
        value=str(DEFAULT_RAG_SCORES_PATH),
        label="RAG scores JSONL path",
        full_width=True,
    )
    rag_answers_path_input = mo.ui.text(
        value=str(DEFAULT_RAG_ANSWERS_PATH),
        label="RAG answers JSONL path",
        full_width=True,
    )
    mo.vstack(
        [
            no_rag_scores_path_input,
            no_rag_answers_path_input,
            rag_scores_path_input,
            rag_answers_path_input,
        ]
    )
    return (
        no_rag_answers_path_input,
        no_rag_scores_path_input,
        rag_answers_path_input,
        rag_scores_path_input,
    )


@app.cell
def _(
    Path,
    no_rag_answers_path_input,
    no_rag_scores_path_input,
    rag_answers_path_input,
    rag_scores_path_input,
    read_jsonl,
):
    no_rag_scores_path = Path(no_rag_scores_path_input.value)
    no_rag_answers_path = Path(no_rag_answers_path_input.value)
    rag_scores_path = Path(rag_scores_path_input.value)
    rag_answers_path = Path(rag_answers_path_input.value)

    no_rag_score_records_raw = list(read_jsonl(no_rag_scores_path))
    no_rag_answer_records_raw = list(read_jsonl(no_rag_answers_path))
    rag_score_records_raw = list(read_jsonl(rag_scores_path))
    rag_answer_records_raw = list(read_jsonl(rag_answers_path))
    return (
        no_rag_answer_records_raw,
        no_rag_score_records_raw,
        rag_answer_records_raw,
        rag_score_records_raw,
    )


@app.cell
def _(
    FAILURE_TYPES,
    no_rag_answer_records_raw,
    no_rag_score_records_raw,
    rag_answer_records_raw,
    rag_score_records_raw,
):
    def pair_key(row):
        return (str(row.get("question_id")), str(row.get("model")))

    def answer_record_key(row):
        return (str(row.get("run_id")), str(row.get("question_id")), str(row.get("model")))

    def sorted_retrieved_contexts(row):
        rag_payload = row.get("rag", {})
        retrieved_contexts = rag_payload.get("retrieved_context", [])
        return sorted(retrieved_contexts, key=lambda context: int(context.get("rank", 10**9)))

    def merge_score_records(score_records, answer_records, answer_set_label):
        answers_by_full_key = {answer_record_key(row): row for row in answer_records}
        answers_by_pair_key = {pair_key(row): row for row in answer_records}
        score_error_rows = [row for row in score_records if row.get("error")]
        scored_rows = [row for row in score_records if not row.get("error") and "score" in row]
        merged_rows = []
        for score_row in sorted(scored_rows, key=lambda row: int(row.get("answer_index", 10**9))):
            answer_row = answers_by_full_key.get(answer_record_key(score_row), answers_by_pair_key.get(pair_key(score_row), {}))
            failure_types = score_row.get("failure_types", {})
            failure_notes = score_row.get("failure_notes", {})
            metadata = score_row.get("question_metadata") or answer_row.get("benchmark_metadata", {})
            retrieved_contexts = sorted_retrieved_contexts(answer_row)
            distances = [
                float(context["distance"])
                for context in retrieved_contexts
                if context.get("distance") is not None
            ]
            top_context = retrieved_contexts[0] if retrieved_contexts else {}
            top_metadata = top_context.get("metadata", {})
            active_failure_types = [
                failure_type
                for failure_type in FAILURE_TYPES
                if failure_types.get(failure_type)
            ]
            merged_rows.append(
                {
                    **score_row,
                    "answer_set": answer_set_label,
                    "question": answer_row.get("question", ""),
                    "answer": answer_row.get("answer", ""),
                    "prompt_version": answer_row.get("prompt_version", ""),
                    "benchmark_metadata": answer_row.get("benchmark_metadata", {}),
                    "active_failure_types": active_failure_types,
                    "active_failure_types_text": ", ".join(active_failure_types),
                    "failure_count": len(active_failure_types),
                    "category": metadata.get("category", ""),
                    "difficulty": metadata.get("difficulty", ""),
                    "answer_status": metadata.get("answer_status", ""),
                    "contentiousness": metadata.get("contentiousness", ""),
                    "verification_status": metadata.get("verification_status", ""),
                    "retrieved_context": retrieved_contexts,
                    "retrieved_context_count": len(retrieved_contexts),
                    "top_distance": distances[0] if distances else None,
                    "avg_distance": sum(distances) / len(distances) if distances else None,
                    "top_source_file": top_metadata.get("source_file", ""),
                    "top_source_name": top_metadata.get("name", ""),
                    "failure_notes_compact": {
                        failure_type: failure_notes.get(failure_type, "")
                        for failure_type in active_failure_types
                        if failure_notes.get(failure_type)
                    },
                }
            )
        return merged_rows, score_error_rows

    no_rag_records, no_rag_score_error_records = merge_score_records(
        no_rag_score_records_raw,
        no_rag_answer_records_raw,
        "no_rag",
    )
    rag_records, rag_score_error_records = merge_score_records(
        rag_score_records_raw,
        rag_answer_records_raw,
        "rag",
    )
    return (
        no_rag_records,
        no_rag_score_error_records,
        pair_key,
        rag_records,
        rag_score_error_records,
    )


@app.cell
def _(no_rag_records, pair_key, rag_records):
    no_rag_by_key = {pair_key(row): row for row in no_rag_records}
    rag_by_key = {pair_key(row): row for row in rag_records}
    shared_keys = sorted(set(no_rag_by_key) & set(rag_by_key))
    no_rag_only_keys = sorted(set(no_rag_by_key) - set(rag_by_key))
    rag_only_keys = sorted(set(rag_by_key) - set(no_rag_by_key))

    pair_records = []
    for question_id, model in shared_keys:
        no_rag_row = no_rag_by_key[(question_id, model)]
        rag_row = rag_by_key[(question_id, model)]
        score_delta = float(rag_row["score"]) - float(no_rag_row["score"])
        no_rag_failures = set(no_rag_row["active_failure_types"])
        rag_failures = set(rag_row["active_failure_types"])
        pair_records.append(
            {
                "question_id": question_id,
                "model": model,
                "question": rag_row.get("question") or no_rag_row.get("question", ""),
                "category": rag_row.get("category") or no_rag_row.get("category", ""),
                "difficulty": rag_row.get("difficulty") or no_rag_row.get("difficulty", ""),
                "answer_status": rag_row.get("answer_status") or no_rag_row.get("answer_status", ""),
                "no_rag": no_rag_row,
                "rag": rag_row,
                "no_rag_score": float(no_rag_row["score"]),
                "rag_score": float(rag_row["score"]),
                "score_delta": score_delta,
                "abs_score_delta": abs(score_delta),
                "no_rag_passed": bool(no_rag_row["passed"]),
                "rag_passed": bool(rag_row["passed"]),
                "pass_transition": f"{'pass' if no_rag_row['passed'] else 'fail'} -> {'pass' if rag_row['passed'] else 'fail'}",
                "no_rag_failure_count": no_rag_row["failure_count"],
                "rag_failure_count": rag_row["failure_count"],
                "failure_count_delta": rag_row["failure_count"] - no_rag_row["failure_count"],
                "new_failure_types": sorted(rag_failures - no_rag_failures),
                "resolved_failure_types": sorted(no_rag_failures - rag_failures),
                "shared_failure_types": sorted(no_rag_failures & rag_failures),
                "changed_failure_types": sorted(no_rag_failures ^ rag_failures),
                "top_source_file": rag_row.get("top_source_file", ""),
                "top_source_name": rag_row.get("top_source_name", ""),
                "top_distance": rag_row.get("top_distance"),
            }
        )
    return no_rag_only_keys, pair_records, rag_only_keys


@app.cell
def _(
    mo,
    no_rag_only_keys,
    no_rag_records,
    no_rag_score_error_records,
    pair_records,
    rag_only_keys,
    rag_records,
    rag_score_error_records,
):
    paired_count = len(pair_records)
    improved_count = sum(1 for row in pair_records if row["score_delta"] > 0)
    declined_count = sum(1 for row in pair_records if row["score_delta"] < 0)
    unchanged_count = paired_count - improved_count - declined_count
    no_rag_pass_count = sum(1 for row in pair_records if row["no_rag_passed"])
    rag_pass_count = sum(1 for row in pair_records if row["rag_passed"])
    average_no_rag_score = sum(row["no_rag_score"] for row in pair_records) / paired_count
    average_rag_score = sum(row["rag_score"] for row in pair_records) / paired_count
    average_score_delta = sum(row["score_delta"] for row in pair_records) / paired_count
    mo.md(f"""
    **Matched answer pairs:** {paired_count} of {len(no_rag_records)} no-RAG rows and {len(rag_records)} RAG rows

    **Average no-RAG score:** {average_no_rag_score:.3f} &nbsp;&nbsp; **Average RAG score:** {average_rag_score:.3f} &nbsp;&nbsp; **Average delta:** {average_score_delta:+.3f}

    **No-RAG pass count:** {no_rag_pass_count} &nbsp;&nbsp; **RAG pass count:** {rag_pass_count}

    **Improved:** {improved_count} &nbsp;&nbsp; **Declined:** {declined_count} &nbsp;&nbsp; **Unchanged:** {unchanged_count}

    **Unmatched no-RAG rows:** {len(no_rag_only_keys)} &nbsp;&nbsp; **Unmatched RAG rows:** {len(rag_only_keys)}

    **Score error rows skipped:** {len(no_rag_score_error_records)} no-RAG, {len(rag_score_error_records)} RAG
    """)
    return


@app.cell
def _(pair_records, pd):
    comparison_df = pd.DataFrame(
        [
            {
                "question_id": row["question_id"],
                "model": row["model"],
                "no_rag_score": row["no_rag_score"],
                "rag_score": row["rag_score"],
                "score_delta": row["score_delta"],
                "pass_transition": row["pass_transition"],
                "no_rag_failure_count": row["no_rag_failure_count"],
                "rag_failure_count": row["rag_failure_count"],
                "failure_count_delta": row["failure_count_delta"],
                "new_failure_types": ", ".join(row["new_failure_types"]),
                "resolved_failure_types": ", ".join(row["resolved_failure_types"]),
                "category": row["category"],
                "difficulty": row["difficulty"],
                "answer_status": row["answer_status"],
                "top_source_file": row["top_source_file"],
                "top_distance": row["top_distance"],
            }
            for row in pair_records
        ]
    )
    comparison_df
    return (comparison_df,)


@app.cell
def _(comparison_df):
    model_delta_df = (
        comparison_df.groupby("model", dropna=False)
        .agg(
            pairs=("question_id", "count"),
            no_rag_avg_score=("no_rag_score", "mean"),
            rag_avg_score=("rag_score", "mean"),
            avg_score_delta=("score_delta", "mean"),
            improved=("score_delta", lambda values: int((values > 0).sum())),
            declined=("score_delta", lambda values: int((values < 0).sum())),
            no_rag_passes=("pass_transition", lambda values: int(values.str.startswith("pass").sum())),
            rag_passes=("pass_transition", lambda values: int(values.str.endswith("pass").sum())),
        )
        .reset_index()
        .sort_values(["avg_score_delta", "model"], ascending=[False, True])
    )
    for score_column in ["no_rag_avg_score", "rag_avg_score", "avg_score_delta"]:
        model_delta_df[score_column] = model_delta_df[score_column].round(3)
    model_delta_df
    return (model_delta_df,)


@app.cell
def _(model_delta_df, plt):
    score_delta_plot_df = model_delta_df.sort_values("avg_score_delta", ascending=True)
    score_delta_fig, score_delta_ax = plt.subplots(figsize=(9, 4.8))
    score_delta_colors = [
        "#3d7f5f" if value >= 0 else "#ad5b53"
        for value in score_delta_plot_df["avg_score_delta"]
    ]
    score_delta_ax.barh(
        score_delta_plot_df["model"],
        score_delta_plot_df["avg_score_delta"],
        color=score_delta_colors,
    )
    score_delta_ax.axvline(0, color="#333333", linewidth=1)
    score_delta_ax.set_title("Average Score Delta by Model")
    score_delta_ax.set_xlabel("RAG score minus no-RAG score")
    score_delta_ax.set_ylabel("")
    score_delta_ax.grid(axis="x", alpha=0.25)
    score_delta_fig.tight_layout()
    score_delta_fig
    return


@app.cell
def _(comparison_df):
    transition_df = (
        comparison_df["pass_transition"]
        .value_counts()
        .rename_axis("pass_transition")
        .reset_index(name="pairs")
        .sort_values(["pass_transition"])
    )
    transition_df
    return (transition_df,)


@app.cell
def _(plt, transition_df):
    transition_fig, transition_ax = plt.subplots(figsize=(6.5, 4.2))
    transition_ax.bar(
        transition_df["pass_transition"],
        transition_df["pairs"],
        color=["#ad5b53", "#7a7a7a", "#3d7f5f", "#4c6f9f"][: len(transition_df)],
    )
    transition_ax.set_title("Pass/Fail Transitions")
    transition_ax.set_xlabel("")
    transition_ax.set_ylabel("Matched pairs")
    transition_ax.grid(axis="y", alpha=0.25)
    transition_fig.tight_layout()
    transition_fig
    return


@app.cell
def _(FAILURE_TYPES, pair_records, pd):
    failure_delta_rows = []
    for failure_type in FAILURE_TYPES:
        no_rag_count = sum(1 for row in pair_records if failure_type in row["no_rag"]["active_failure_types"])
        rag_count = sum(1 for row in pair_records if failure_type in row["rag"]["active_failure_types"])
        new_count = sum(1 for row in pair_records if failure_type in row["new_failure_types"])
        resolved_count = sum(1 for row in pair_records if failure_type in row["resolved_failure_types"])
        failure_delta_rows.append(
            {
                "failure_type": failure_type,
                "no_rag_count": no_rag_count,
                "rag_count": rag_count,
                "count_delta": rag_count - no_rag_count,
                "new_in_rag": new_count,
                "resolved_by_rag": resolved_count,
            }
        )
    failure_delta_df = pd.DataFrame(failure_delta_rows).sort_values(
        ["count_delta", "failure_type"],
        ascending=[True, True],
    )
    failure_delta_df
    return (failure_delta_df,)


@app.cell
def _(failure_delta_df, plt):
    failure_delta_plot_df = failure_delta_df.sort_values("count_delta", ascending=True)
    failure_delta_fig, failure_delta_ax = plt.subplots(figsize=(9, 4.8))
    failure_delta_colors = [
        "#3d7f5f" if value <= 0 else "#ad5b53"
        for value in failure_delta_plot_df["count_delta"]
    ]
    failure_delta_ax.barh(
        failure_delta_plot_df["failure_type"],
        failure_delta_plot_df["count_delta"],
        color=failure_delta_colors,
    )
    failure_delta_ax.axvline(0, color="#333333", linewidth=1)
    failure_delta_ax.set_title("Failure Type Count Delta")
    failure_delta_ax.set_xlabel("RAG count minus no-RAG count")
    failure_delta_ax.set_ylabel("")
    failure_delta_ax.grid(axis="x", alpha=0.25)
    failure_delta_fig.tight_layout()
    failure_delta_fig
    return


@app.cell
def _(comparison_df):
    biggest_improvements_df = comparison_df.sort_values(
        ["score_delta", "question_id", "model"],
        ascending=[False, True, True],
    ).head(20)
    biggest_improvements_df
    return


@app.cell
def _(comparison_df):
    biggest_declines_df = comparison_df.sort_values(
        ["score_delta", "question_id", "model"],
        ascending=[True, True, True],
    ).head(20)
    biggest_declines_df
    return


@app.cell
def _(FAILURE_TYPES, mo, pair_records):
    model_options = ["All models"] + sorted({row["model"] for row in pair_records})
    transition_options = ["All transitions"] + sorted({row["pass_transition"] for row in pair_records})
    failure_change_options = [
        "Any failure change",
        "Any new RAG failure",
        "Any resolved no-RAG failure",
        "No failure change",
    ] + list(FAILURE_TYPES)
    score_delta_options = [
        "All score deltas",
        "RAG improved",
        "RAG declined",
        "Unchanged score",
        "Absolute delta >= 0.25",
        "Absolute delta >= 0.50",
    ]

    model_dropdown = mo.ui.dropdown(options=model_options, value="All models", label="Answer model")
    transition_dropdown = mo.ui.dropdown(
        options=transition_options,
        value="All transitions",
        label="Pass transition",
    )
    failure_change_dropdown = mo.ui.dropdown(
        options=failure_change_options,
        value="Any failure change",
        label="Failure change",
    )
    score_delta_dropdown = mo.ui.dropdown(
        options=score_delta_options,
        value="All score deltas",
        label="Score delta",
    )
    question_filter_input = mo.ui.text(value="", label="Question ID contains", full_width=True)
    mo.vstack(
        [
            mo.hstack([model_dropdown, transition_dropdown]),
            mo.hstack([failure_change_dropdown, score_delta_dropdown]),
            question_filter_input,
        ]
    )
    return (
        failure_change_dropdown,
        model_dropdown,
        question_filter_input,
        score_delta_dropdown,
        transition_dropdown,
    )


@app.cell
def _(
    failure_change_dropdown,
    model_dropdown,
    pair_records,
    question_filter_input,
    score_delta_dropdown,
    transition_dropdown,
):
    question_filter = question_filter_input.value.strip().lower()
    filtered_pairs = []
    for candidate_pair in pair_records:
        if model_dropdown.value != "All models" and candidate_pair["model"] != model_dropdown.value:
            continue
        if transition_dropdown.value != "All transitions" and candidate_pair["pass_transition"] != transition_dropdown.value:
            continue
        if question_filter and question_filter not in candidate_pair["question_id"].lower():
            continue
        if score_delta_dropdown.value == "RAG improved" and candidate_pair["score_delta"] <= 0:
            continue
        if score_delta_dropdown.value == "RAG declined" and candidate_pair["score_delta"] >= 0:
            continue
        if score_delta_dropdown.value == "Unchanged score" and candidate_pair["score_delta"] != 0:
            continue
        if score_delta_dropdown.value == "Absolute delta >= 0.25" and candidate_pair["abs_score_delta"] < 0.25:
            continue
        if score_delta_dropdown.value == "Absolute delta >= 0.50" and candidate_pair["abs_score_delta"] < 0.50:
            continue
        if failure_change_dropdown.value == "Any failure change" and not candidate_pair["changed_failure_types"]:
            continue
        if failure_change_dropdown.value == "Any new RAG failure" and not candidate_pair["new_failure_types"]:
            continue
        if failure_change_dropdown.value == "Any resolved no-RAG failure" and not candidate_pair["resolved_failure_types"]:
            continue
        if failure_change_dropdown.value == "No failure change" and candidate_pair["changed_failure_types"]:
            continue
        if failure_change_dropdown.value not in {
            "Any failure change",
            "Any new RAG failure",
            "Any resolved no-RAG failure",
            "No failure change",
        }:
            if failure_change_dropdown.value not in candidate_pair["changed_failure_types"]:
                continue
        filtered_pairs.append(candidate_pair)
    return (filtered_pairs,)


@app.cell
def _(mo):
    page_size_dropdown = mo.ui.dropdown(
        options=["10", "25", "50", "100"],
        value="25",
        label="Pairs per page",
    )
    page_number_input = mo.ui.text(value="1", label="Page number")
    mo.hstack([page_size_dropdown, page_number_input])
    return page_number_input, page_size_dropdown


@app.cell
def _(filtered_pairs, page_number_input, page_size_dropdown):
    page_size = int(page_size_dropdown.value)
    total_pages = max(1, (len(filtered_pairs) + page_size - 1) // page_size)
    page_text = page_number_input.value.strip()
    requested_page = int(page_text) if page_text.isdecimal() else 1
    page_number = min(max(1, requested_page), total_pages)
    start_offset = (page_number - 1) * page_size
    page_pairs = filtered_pairs[start_offset : start_offset + page_size]
    return page_number, page_pairs, start_offset, total_pages


@app.cell
def _(filtered_pairs, mo, page_number, total_pages):
    mo.md(f"""
    **Filtered pairs:** {len(filtered_pairs)} &nbsp;&nbsp; **Page:** {page_number} of {total_pages}
    """)
    return


@app.cell
def _(page_pairs, pd, start_offset):
    page_pairs_df = pd.DataFrame(
        [
            {
                "row": start_offset + index,
                "question_id": row["question_id"],
                "model": row["model"],
                "no_rag_score": row["no_rag_score"],
                "rag_score": row["rag_score"],
                "score_delta": row["score_delta"],
                "pass_transition": row["pass_transition"],
                "new_failure_types": ", ".join(row["new_failure_types"]),
                "resolved_failure_types": ", ".join(row["resolved_failure_types"]),
                "top_source_file": row["top_source_file"],
            }
            for index, row in enumerate(page_pairs)
        ]
    )
    page_pairs_df
    return


@app.cell
def _(mo, page_pairs, start_offset):
    pair_options = [
        (
            f"{start_offset + index}: {row['question_id']} | {row['model']} | "
            f"{row['no_rag_score']:.2f} -> {row['rag_score']:.2f} "
            f"({row['score_delta']:+.2f}) | {row['pass_transition']}"
        )
        for index, row in enumerate(page_pairs)
    ]
    pair_options = pair_options or ["No matching pairs"]
    selected_pair_dropdown = mo.ui.dropdown(
        options=pair_options,
        value=pair_options[0],
        label="Select pair on this page",
        full_width=True,
    )
    selected_pair_dropdown
    return pair_options, selected_pair_dropdown


@app.cell
def _(page_pairs, pair_options, selected_pair_dropdown):
    if page_pairs and selected_pair_dropdown.value in pair_options:
        selected_pair_index = pair_options.index(selected_pair_dropdown.value)
        selected_pair = page_pairs[selected_pair_index]
    else:
        selected_pair = {}
    selected_no_rag_record = selected_pair.get("no_rag", {})
    selected_rag_record = selected_pair.get("rag", {})
    return selected_no_rag_record, selected_pair, selected_rag_record


@app.cell
def _(pd, selected_pair):
    selected_pair_summary_df = pd.DataFrame(
        [
            {
                "question_id": selected_pair.get("question_id", ""),
                "model": selected_pair.get("model", ""),
                "no_rag_score": selected_pair.get("no_rag_score", ""),
                "rag_score": selected_pair.get("rag_score", ""),
                "score_delta": selected_pair.get("score_delta", ""),
                "pass_transition": selected_pair.get("pass_transition", ""),
                "no_rag_failure_count": selected_pair.get("no_rag_failure_count", ""),
                "rag_failure_count": selected_pair.get("rag_failure_count", ""),
                "new_failure_types": ", ".join(selected_pair.get("new_failure_types", [])),
                "resolved_failure_types": ", ".join(selected_pair.get("resolved_failure_types", [])),
                "category": selected_pair.get("category", ""),
                "difficulty": selected_pair.get("difficulty", ""),
                "answer_status": selected_pair.get("answer_status", ""),
            }
        ]
    )
    selected_pair_summary_df
    return


app._unparsable_cell(
    """
    mo.md(f\"\"\"
    ### Question

    {selected_pair.get(\"question\", \"\\\")}
    \"\"\")
    """,
    name="_"
)


@app.cell
def _(mo, selected_no_rag_record, selected_rag_record):
    no_rag_answer_view = mo.ui.text_area(
        value=selected_no_rag_record.get("answer", ""),
        rows=16,
        label="No-RAG answer",
        disabled=True,
        full_width=True,
    )
    rag_answer_view = mo.ui.text_area(
        value=selected_rag_record.get("answer", ""),
        rows=16,
        label="RAG answer",
        disabled=True,
        full_width=True,
    )
    mo.hstack([no_rag_answer_view, rag_answer_view], widths="equal")
    return


@app.cell
def _(mo, selected_no_rag_record, selected_rag_record):
    no_rag_rationale_view = mo.ui.text_area(
        value=selected_no_rag_record.get("rationale", ""),
        rows=10,
        label="No-RAG judge rationale",
        disabled=True,
        full_width=True,
    )
    rag_rationale_view = mo.ui.text_area(
        value=selected_rag_record.get("rationale", ""),
        rows=10,
        label="RAG judge rationale",
        disabled=True,
        full_width=True,
    )
    mo.hstack([no_rag_rationale_view, rag_rationale_view], widths="equal")
    return


@app.cell
def _(FAILURE_TYPES, pd, selected_no_rag_record, selected_rag_record):
    selected_failure_comparison_df = pd.DataFrame(
        [
            {
                "failure_type": failure_type,
                "no_rag_present": bool(selected_no_rag_record.get("failure_types", {}).get(failure_type)),
                "rag_present": bool(selected_rag_record.get("failure_types", {}).get(failure_type)),
                "changed": bool(selected_no_rag_record.get("failure_types", {}).get(failure_type))
                != bool(selected_rag_record.get("failure_types", {}).get(failure_type)),
                "no_rag_note": selected_no_rag_record.get("failure_notes", {}).get(failure_type, ""),
                "rag_note": selected_rag_record.get("failure_notes", {}).get(failure_type, ""),
            }
            for failure_type in FAILURE_TYPES
        ]
    )
    selected_failure_comparison_df
    return


@app.cell
def _(pd, selected_rag_record):
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
            for context in selected_rag_record.get("retrieved_context", [])
        ]
    )
    selected_context_df
    return


@app.cell
def _(mo, selected_rag_record):
    context_options = [
        (
            f"{context.get('rank', '')}: "
            f"{context.get('metadata', {}).get('source_file', '')} | "
            f"{context.get('metadata', {}).get('name', '')} | "
            f"distance={float(context.get('distance', 0.0)):.3f}"
        )
        for context in selected_rag_record.get("retrieved_context", [])
    ]
    context_options = context_options or ["No retrieved context"]
    selected_context_dropdown = mo.ui.dropdown(
        options=context_options,
        value=context_options[0],
        label="Select RAG retrieved context",
        full_width=True,
    )
    selected_context_dropdown
    return context_options, selected_context_dropdown


@app.cell
def _(context_options, selected_context_dropdown, selected_rag_record):
    selected_retrieved_contexts = selected_rag_record.get("retrieved_context", [])
    if selected_retrieved_contexts and selected_context_dropdown.value in context_options:
        selected_context_index = context_options.index(selected_context_dropdown.value)
        selected_context = selected_retrieved_contexts[selected_context_index]
    else:
        selected_context = {}
    return (selected_context,)


@app.cell
def _(json, mo, selected_context):
    selected_context_text = mo.ui.text_area(
        value=selected_context.get("text", ""),
        rows=12,
        label="RAG retrieved context text",
        disabled=True,
        full_width=True,
    )
    selected_context_metadata = mo.ui.text_area(
        value=json.dumps(selected_context.get("metadata", {}), ensure_ascii=False, indent=2, sort_keys=True),
        rows=8,
        label="RAG retrieved context metadata",
        disabled=True,
        full_width=True,
    )
    mo.vstack([selected_context_text, selected_context_metadata])
    return


@app.cell
def _(json, mo, selected_no_rag_record, selected_rag_record):
    no_rag_json_preview = mo.ui.text_area(
        value=json.dumps(selected_no_rag_record, ensure_ascii=False, indent=2, sort_keys=True),
        rows=12,
        label="Selected no-RAG merged record JSON",
        disabled=True,
        full_width=True,
    )
    rag_json_preview = mo.ui.text_area(
        value=json.dumps(selected_rag_record, ensure_ascii=False, indent=2, sort_keys=True),
        rows=12,
        label="Selected RAG merged record JSON",
        disabled=True,
        full_width=True,
    )
    mo.hstack([no_rag_json_preview, rag_json_preview], widths="equal")
    return


if __name__ == "__main__":
    app.run()
