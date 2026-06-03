# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "langchain-openrouter>=0.2.3",
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
    import os
    import uuid
    from datetime import UTC, datetime
    from pathlib import Path

    import marimo as mo
    import pandas as pd
    from dotenv import load_dotenv
    from langchain_openrouter import ChatOpenRouter

    return (
        ChatOpenRouter,
        Path,
        UTC,
        datetime,
        json,
        load_dotenv,
        mo,
        os,
        pd,
        uuid,
    )


@app.cell
def _(mo):
    mo.md("""
    # LangChain answer gathering demo

    This notebook demonstrates the no-RAG answer gathering flow using LangChain's
    OpenRouter chat integration. It reads the local benchmark, sends selected
    questions to a model, and builds workbook-style records compatible with the
    file-based evaluation pipeline.
    """)
    return


@app.cell
def _(Path):
    NOTEBOOK_DIR = Path(__file__).parent
    BENCHMARK_PATH = NOTEBOOK_DIR / "Resources" / "Test files" / "benchmark.jsonl"
    ENV_PATH = NOTEBOOK_DIR / ".env"
    return BENCHMARK_PATH, ENV_PATH


@app.cell
def _(ENV_PATH, load_dotenv, mo):
    load_dotenv(ENV_PATH, override=False)
    is_script_mode = mo.app_meta().mode == "script"
    return (is_script_mode,)


@app.cell
def _(json):
    PROMPT_VERSION = "langchain-no-rag-demo-v1"
    PIPELINE_NAME = "no_rag_langchain_demo"

    METADATA_KEYS = [
        "category",
        "difficulty",
        "answer_status",
        "contentiousness",
        "curation_status",
        "verification_status",
        "version_specificity",
        "gold_dataset_linked",
        "gold_link_status",
        "linked_gold_ids",
        "tags",
        "topic",
    ]

    SYSTEM_PROMPT = """You answer questions about D&D SRD 5.2.1 rules.

    Answer from your own knowledge, but keep the response scoped to SRD 5.2.1.
    Do not import Pathfinder, D&D 2014, forum rulings, or non-SRD 2024 material.
    When SRD 5.2.1 may differ from older 2014 D&D rules, prefer SRD 5.2.1 and say when you are uncertain.
    If the SRD answer is uncertain or ambiguous, say so plainly.
    Do not cite page numbers, book sections, or quoted rules text unless those details were provided in the question.
    If you are relying on memory, explain the rule without citations."""

    def read_jsonl(path):
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8-sig").splitlines()
            if line.strip()
        ]

    def compact_metadata(row):
        return {key: row[key] for key in METADATA_KEYS if key in row}

    def make_user_prompt(row):
        return f"""Question:
    {row["question"]}"""

    return (
        PIPELINE_NAME,
        PROMPT_VERSION,
        SYSTEM_PROMPT,
        compact_metadata,
        make_user_prompt,
        read_jsonl,
    )


@app.cell
def _(BENCHMARK_PATH, read_jsonl):
    benchmark_rows = read_jsonl(BENCHMARK_PATH)
    return (benchmark_rows,)


@app.cell
def _(benchmark_rows, pd):
    benchmark_df = pd.DataFrame(
        [
            {
                "id": row["id"],
                "difficulty": row.get("difficulty"),
                "category": row.get("category"),
                "question": row["question"],
            }
            for row in benchmark_rows
        ]
    )
    benchmark_df.head(8)
    return


@app.cell
def _(mo, os):
    default_model = os.environ.get("OPENROUTER_MODELS", "openrouter/owl-alpha").split(",")[0].strip()
    model_input = mo.ui.text(value=default_model, label="OpenRouter model")
    limit_slider = mo.ui.slider(start=1, stop=10, value=3, label="Question limit")
    max_tokens_slider = mo.ui.slider(start=256, stop=2400, step=128, value=1024, label="Max tokens")
    temperature_slider = mo.ui.slider(start=0.0, stop=1.0, step=0.1, value=0.0, label="Temperature")
    run_button = mo.ui.run_button(label="Gather answers")
    mo.vstack([model_input, limit_slider, max_tokens_slider, temperature_slider, run_button])
    return (
        limit_slider,
        max_tokens_slider,
        model_input,
        run_button,
        temperature_slider,
    )


@app.cell
def _(ChatOpenRouter, max_tokens_slider, model_input, os, temperature_slider):
    def make_chat_model():
        return ChatOpenRouter(
            model=model_input.value,
            temperature=temperature_slider.value,
            max_tokens=max_tokens_slider.value,
            api_key=os.environ.get("OPENROUTER_API_KEY"),
            app_url=os.environ.get("OPENROUTER_SITE_URL") or None,
            app_title="SRD rules agent LangChain gathering demo",
        )

    return (make_chat_model,)


@app.cell
def _(
    PIPELINE_NAME,
    PROMPT_VERSION,
    SYSTEM_PROMPT,
    UTC,
    compact_metadata,
    datetime,
    json,
    make_chat_model,
    make_user_prompt,
    mo,
    model_input,
    uuid,
):
    def response_text(message):
        content = message.content
        if isinstance(content, str):
            return content
        return json.dumps(content, ensure_ascii=False)

    def make_record(run_id, row, answer, raw_response=None):
        return {
            "run_id": run_id,
            "pipeline": PIPELINE_NAME,
            "question_id": row["id"],
            "model": model_input.value,
            "prompt_version": PROMPT_VERSION,
            "question": row["question"],
            "answer": answer,
            "benchmark_metadata": compact_metadata(row),
            "raw_response": raw_response or {},
            "generated_at": datetime.now(UTC).isoformat(),
        }

    def gather_with_langchain(rows):
        run_id = f"notebook-no-rag-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
        model = make_chat_model()
        records = []
        with mo.status.progress_bar(
            total=len(rows),
            title="Gathering answers",
            subtitle=f"Starting {len(rows)} request(s) with {model_input.value}",
            completion_title="Answer gathering complete",
            completion_subtitle=f"Collected {len(rows)} answer record(s)",
            remove_on_exit=False,
        ) as progress:
            for row in rows:
                progress.update(increment=0, subtitle=f"Requesting {row['id']}")
                message = model.invoke(
                    [
                        ("system", SYSTEM_PROMPT),
                        ("human", make_user_prompt(row)),
                    ]
                )
                records.append(make_record(run_id, row, response_text(message), message.model_dump()))
                progress.update(subtitle=f"Collected {row['id']}")
        return records

    def gather_dry_run(rows):
        run_id = f"notebook-dry-run-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
        return [
            make_record(
                run_id,
                row,
                "Dry run placeholder: open the notebook interactively and click Gather answers.",
            )
            for row in rows
        ]

    return gather_dry_run, gather_with_langchain


@app.cell
def _(
    benchmark_rows,
    gather_dry_run,
    gather_with_langchain,
    is_script_mode,
    limit_slider,
    run_button,
):
    selected_rows = benchmark_rows[: limit_slider.value]
    gather_mode = "dry-run"
    if is_script_mode:
        answer_records = gather_dry_run(selected_rows)
    elif run_button.value:
        answer_records = gather_with_langchain(selected_rows)
        gather_mode = "live"
    else:
        answer_records = gather_dry_run(selected_rows)
    return answer_records, gather_mode, selected_rows


@app.cell
def _(answer_records, gather_mode, mo, selected_rows):
    mo.md(f"""
    **Gather status:** `{gather_mode}` mode produced **{len(answer_records)}**
    record(s) for **{len(selected_rows)}** selected question(s).
    """)
    return


@app.cell
def _(answer_records, pd):
    def truncate(text, limit=220):
        compact = " ".join(str(text).split())
        return compact if len(compact) <= limit else f"{compact[:limit]}..."

    answer_preview_df = pd.DataFrame(
        [
            {
                "question_id": record["question_id"],
                "model": record["model"],
                "answer_preview": truncate(record["answer"]),
            }
            for record in answer_records
        ]
    )
    answer_preview_df
    return


@app.cell
def _(answer_records, json, mo):
    workbook_jsonl = "\n".join(json.dumps(record, ensure_ascii=False) for record in answer_records)
    jsonl_preview = mo.ui.text_area(
        value=workbook_jsonl,
        rows=14,
        label="Workbook JSONL preview",
        disabled=True,
        full_width=True,
    )
    jsonl_preview
    return


if __name__ == "__main__":
    app.run()
