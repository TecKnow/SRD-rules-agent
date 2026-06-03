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
    import asyncio
    import json
    import os
    from datetime import UTC, datetime
    from pathlib import Path

    import marimo as mo
    import pandas as pd
    from dotenv import load_dotenv

    from srd_eval.grade_deepeval import (
        DEFAULT_THRESHOLD,
        DEFAULT_CONCURRENCY,
        EVALUATOR_NAME,
        EVALUATOR_VERSION,
        FAILURE_TYPES,
        StructuredOpenRouterJudge,
        benchmark_by_id,
        default_output_path,
        normalize_diagnostic_result,
        validate_answers,
    )
    from srd_eval.io import read_jsonl

    return (
        DEFAULT_CONCURRENCY,
        DEFAULT_THRESHOLD,
        EVALUATOR_NAME,
        EVALUATOR_VERSION,
        FAILURE_TYPES,
        Path,
        StructuredOpenRouterJudge,
        UTC,
        asyncio,
        benchmark_by_id,
        datetime,
        default_output_path,
        json,
        load_dotenv,
        mo,
        normalize_diagnostic_result,
        os,
        pd,
        read_jsonl,
        validate_answers,
    )


@app.cell
def _(mo):
    mo.md("""
    # DeepEval judging smoke test

    This notebook exercises the structured grading workflow on a small answer
    sample. It validates the answer workbook, builds score records with the same
    diagnostic fields as the grader, and lets you inspect scores, failure flags,
    notes, and JSONL-shaped output before a full grading run.
    """)
    return


@app.cell
def _(Path):
    NOTEBOOK_DIR = Path(__file__).parent
    BENCHMARK_PATH = NOTEBOOK_DIR / "Resources" / "Test files" / "benchmark.jsonl"
    DEFAULT_ANSWERS_PATH = (
        NOTEBOOK_DIR
        / "runs"
        / "no_rag"
        / "no-rag-20260603T074521Z-07aa8696"
        / "answers_for_grading.jsonl"
    )
    ENV_PATH = NOTEBOOK_DIR / ".env"
    return BENCHMARK_PATH, DEFAULT_ANSWERS_PATH, ENV_PATH


@app.cell
def _(ENV_PATH, load_dotenv, mo):
    load_dotenv(ENV_PATH, override=False)
    is_script_mode = mo.app_meta().mode == "script"
    return (is_script_mode,)


@app.cell
def _(BENCHMARK_PATH, benchmark_by_id):
    benchmark = benchmark_by_id(BENCHMARK_PATH)
    return (benchmark,)


@app.cell
def _(DEFAULT_ANSWERS_PATH, DEFAULT_CONCURRENCY, DEFAULT_THRESHOLD, mo, os):
    answers_path_input = mo.ui.text(
        value=str(DEFAULT_ANSWERS_PATH),
        label="Answers JSONL path",
        full_width=True,
    )
    judge_model_input = mo.ui.text(
        value=os.environ.get("DEEPEVAL_JUDGE_MODEL", "openai/gpt-5.5"),
        label="Judge model",
        full_width=True,
    )
    question_ids_input = mo.ui.text(
        value="",
        label="Question IDs, comma-separated",
        full_width=True,
    )
    model_filter_input = mo.ui.text(
        value="",
        label="Answer model contains",
        full_width=True,
    )
    start_index_input = mo.ui.text(
        value="0",
        label="Start row index after filters",
    )
    limit_slider = mo.ui.slider(start=1, stop=10, value=3, label="Smoke-test rows")
    threshold_slider = mo.ui.slider(
        start=0.0,
        stop=1.0,
        step=0.05,
        value=DEFAULT_THRESHOLD,
        label="Pass threshold",
    )
    timeout_slider = mo.ui.slider(start=30, stop=240, step=30, value=120, label="Timeout seconds")
    concurrency_slider = mo.ui.slider(
        start=1,
        stop=10,
        value=DEFAULT_CONCURRENCY,
        label="Concurrent judge calls",
    )
    run_button = mo.ui.run_button(label="Run live judging sample")
    mo.vstack(
        [
            answers_path_input,
            judge_model_input,
            question_ids_input,
            mo.hstack([model_filter_input, start_index_input]),
            mo.hstack([limit_slider, threshold_slider, timeout_slider, concurrency_slider]),
            run_button,
        ]
    )
    return (
        answers_path_input,
        concurrency_slider,
        judge_model_input,
        limit_slider,
        model_filter_input,
        question_ids_input,
        run_button,
        start_index_input,
        threshold_slider,
        timeout_slider,
    )


@app.cell
def _(Path, answers_path_input, read_jsonl):
    answers_path = Path(answers_path_input.value)
    answer_records = list(read_jsonl(answers_path))
    return answer_records, answers_path


@app.cell
def _(answer_records, benchmark, validate_answers):
    validate_answers(answer_records, benchmark)
    validated_record_count = len(answer_records)
    return (validated_record_count,)


@app.cell
def _(
    answer_records,
    limit_slider,
    model_filter_input,
    question_ids_input,
    start_index_input,
):
    requested_question_ids = {
        item.strip()
        for item in question_ids_input.value.split(",")
        if item.strip()
    }
    model_filter = model_filter_input.value.strip().lower()
    start_index_text = start_index_input.value.strip()
    start_index = int(start_index_text) if start_index_text.isdecimal() else 0

    filtered_answers = [
        answer
        for answer in answer_records
        if not requested_question_ids or str(answer["question_id"]) in requested_question_ids
    ]
    filtered_answers = [
        answer
        for answer in filtered_answers
        if not model_filter or model_filter in str(answer["model"]).lower()
    ]
    selected_answers = filtered_answers[start_index : start_index + limit_slider.value]
    return filtered_answers, selected_answers, start_index


@app.cell
def _(
    filtered_answers,
    mo,
    selected_answers,
    start_index,
    validated_record_count,
):
    mo.md(f"""
    **Input status:** validated **{validated_record_count}** answer record(s).

    **Filter status:** **{len(filtered_answers)}** matching row(s), starting at
    filtered row index **{start_index}**.

    **Selected sample:** **{len(selected_answers)}** row(s).
    """)
    return


@app.cell
def _(pd, selected_answers):
    def compact_text(text, limit=160):
        compact = " ".join(str(text).split())
        return compact if len(compact) <= limit else f"{compact[:limit]}..."

    answer_preview_df = pd.DataFrame(
        [
            {
                "question_id": row["question_id"],
                "model": row["model"],
                "question": compact_text(row["question"], 90),
                "answer_preview": compact_text(row["answer"]),
            }
            for row in selected_answers
        ]
    )
    answer_preview_df
    return


@app.cell
def _(
    EVALUATOR_NAME,
    EVALUATOR_VERSION,
    FAILURE_TYPES,
    StructuredOpenRouterJudge,
    UTC,
    asyncio,
    benchmark,
    concurrency_slider,
    datetime,
    judge_model_input,
    normalize_diagnostic_result,
    threshold_slider,
    timeout_slider,
):
    def active_failure_types(failure_types):
        return [name for name in FAILURE_TYPES if failure_types.get(name)]

    def make_score_record(answer, diagnostic_result):
        score = float(diagnostic_result["score"])
        return {
            "run_id": answer["run_id"],
            "pipeline": answer.get("pipeline", "no_rag"),
            "question_id": str(answer["question_id"]),
            "model": answer["model"],
            "evaluator": EVALUATOR_NAME,
            "evaluator_version": EVALUATOR_VERSION,
            "judge_model": judge_model_input.value,
            "judge_provider": "openrouter",
            "threshold": threshold_slider.value,
            "score": score,
            "passed": score >= threshold_slider.value,
            "rationale": diagnostic_result["rationale"],
            "failure_types": diagnostic_result["failure_types"],
            "failure_notes": diagnostic_result["failure_notes"],
            "diagnostic_confidence": diagnostic_result["diagnostic_confidence"],
            "question_metadata": answer.get("benchmark_metadata", {}),
            "graded_at": datetime.now(UTC).isoformat(),
        }

    def dry_judge(answer):
        diagnostic_result = normalize_diagnostic_result(
            {
                "score": 1.0,
                "rationale": "Dry-run placeholder; click the run button in interactive mode to call the judge.",
                "failure_types": {},
                "failure_notes": {},
                "diagnostic_confidence": "low",
            }
        )
        return make_score_record(answer, diagnostic_result)

    async def live_judge(answers, mo):
        judge = StructuredOpenRouterJudge(
            model=judge_model_input.value,
            timeout_seconds=timeout_slider.value,
        )
        records = [None] * len(answers)
        semaphore = asyncio.Semaphore(concurrency_slider.value)

        async def judge_one(index, answer):
            async with semaphore:
                benchmark_row = benchmark[str(answer["question_id"])]
                diagnostic_result = await judge.ameasure(answer=answer, benchmark_row=benchmark_row)
                return index, make_score_record(answer, diagnostic_result)

        tasks = [judge_one(index, answer) for index, answer in enumerate(answers)]
        with mo.status.progress_bar(
            total=len(tasks),
            title="Judging answers",
            subtitle=f"Starting {len(tasks)} request(s) with {judge_model_input.value}",
            completion_title="Judging complete",
            completion_subtitle=f"Scored {len(tasks)} answer record(s)",
            remove_on_exit=False,
        ) as progress:
            for completed in asyncio.as_completed(tasks):
                index, record = await completed
                records[index] = record
                progress.update(increment=1, subtitle=f"Scored {record['question_id']} | {record['model']}")
        return records

    return active_failure_types, dry_judge, live_judge


@app.cell
async def _(
    dry_judge,
    is_script_mode,
    live_judge,
    mo,
    run_button,
    selected_answers,
):
    judging_mode = "dry-run"
    if is_script_mode:
        score_records = [dry_judge(answer) for answer in selected_answers]
    elif run_button.value:
        score_records = await live_judge(selected_answers, mo)
        judging_mode = "live"
    else:
        score_records = [dry_judge(answer) for answer in selected_answers]
    return judging_mode, score_records


@app.cell
def _(judging_mode, mo, score_records):
    mo.md(f"""
    **Judging status:** `{judging_mode}` mode produced **{len(score_records)}**
    score record(s).
    """)
    return


@app.cell
def _(active_failure_types, pd, score_records):
    score_preview_df = pd.DataFrame(
        [
            {
                "question_id": row["question_id"],
                "answer_model": row["model"],
                "score": row["score"],
                "passed": row["passed"],
                "confidence": row["diagnostic_confidence"],
                "active_failure_types": ", ".join(active_failure_types(row["failure_types"])),
                "rationale": row["rationale"],
            }
            for row in score_records
        ]
    )
    score_preview_df
    return


@app.cell
def _(FAILURE_TYPES, pd, score_records):
    failure_counts_df = pd.DataFrame(
        [
            {
                "failure_type": failure_type,
                "count": sum(1 for row in score_records if row["failure_types"].get(failure_type)),
            }
            for failure_type in FAILURE_TYPES
        ]
    )
    failure_counts_df
    return


@app.cell
def _(FAILURE_TYPES, pd, score_records):
    failure_notes_df = pd.DataFrame(
        [
            {
                "question_id": row["question_id"],
                "failure_type": failure_type,
                "note": row["failure_notes"].get(failure_type, ""),
            }
            for row in score_records
            for failure_type in FAILURE_TYPES
            if row["failure_notes"].get(failure_type)
        ]
    )
    failure_notes_df
    return


@app.cell
def _(json, mo, score_records):
    score_jsonl = "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in score_records)
    score_jsonl_preview = mo.ui.text_area(
        value=score_jsonl,
        rows=14,
        label="Score JSONL preview",
        disabled=True,
        full_width=True,
    )
    score_jsonl_preview
    return


@app.cell
def _(answers_path, default_output_path, mo):
    mo.md(f"""
    **Default full-run output path:** `{default_output_path(answers_path)}`

    The notebook does not write score files; it only previews score records.
    """)
    return


if __name__ == "__main__":
    app.run()
