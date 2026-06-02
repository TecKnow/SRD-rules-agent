# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "marimo[recommended]>=0.23.8",
#     "pandas",
# ]
# ///

import marimo

__generated_with = "0.23.8"
app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path

    import marimo as mo
    import pandas as pd

    return Path, mo, pd


@app.cell
def _(mo):
    mo.md("""
    # D&D 5e SRD QA Dataset

    "
        "Explore the repository-local copy of the Hugging Face dataset "
        "[`datapizza-ai-lab/dnd5e-srd-qa`](https://huggingface.co/datasets/datapizza-ai-lab/dnd5e-srd-qa), "
        "a small QA benchmark for RAG systems built from the D&D 5e SRD.
    """)
    return


@app.cell
def _(Path):
    NOTEBOOK_DIR = Path(__file__).parent
    DATA_DIR = NOTEBOOK_DIR / "data" / "dnd5e-srd-qa"
    CONFIG_FILES = {
        "easy": DATA_DIR / "easy.json",
        "medium": DATA_DIR / "medium.json",
    }
    SOURCE_DOCS_DIR = DATA_DIR / "dnd_srd_docs"
    return CONFIG_FILES, SOURCE_DOCS_DIR


@app.cell
def _(SOURCE_DOCS_DIR):
    def merge_passage_spans(passages):
        ranges_by_document = {}
        for passage in passages:
            ranges_by_document.setdefault(passage["document_path"], []).append(
                (passage["start_char"], passage["end_char"])
            )

        merged_passages = []
        for document_path, ranges in sorted(ranges_by_document.items()):
            merged_ranges = []
            for start_char, end_char in sorted(ranges):
                if not merged_ranges or start_char > merged_ranges[-1][1]:
                    merged_ranges.append([start_char, end_char])
                else:
                    merged_ranges[-1][1] = max(merged_ranges[-1][1], end_char)

            source_text = (SOURCE_DOCS_DIR / document_path).read_text(
                encoding="utf-8"
            )
            for start_char, end_char in merged_ranges:
                merged_passages.append(
                    {
                        "document_path": document_path,
                        "start_char": start_char,
                        "end_char": end_char,
                        "content": source_text[start_char:end_char],
                    }
                )

        return merged_passages

    return (merge_passage_spans,)


@app.cell
def _(CONFIG_FILES, pd):
    frames = []

    for tier, dataset_path in CONFIG_FILES.items():
        frame = pd.read_json(dataset_path)
        frame.insert(0, "tier", tier)
        frames.append(frame)

    qa_df = pd.concat(frames, ignore_index=True)
    qa_df["passage_count"] = qa_df["passages"].map(len)
    return (qa_df,)


@app.cell
def _(mo, qa_df):
    mo.md(f"""
    Loaded **{len(qa_df):,}** question-answer rows across "
        f"**{qa_df['tier'].nunique()}** difficulty tiers.
    """)
    return


@app.cell
def _(qa_df):
    summary_df = (
        qa_df.groupby("tier")
        .agg(
            rows=("id", "count"),
            avg_passages=("passage_count", "mean"),
        )
        .round(1)
        .reset_index()
    )

    summary_df
    return


@app.cell
def _(mo, qa_df):
    tier_filter = mo.ui.dropdown(
        options=["all", *sorted(qa_df["tier"].unique())],
        value="all",
        label="Difficulty tier",
    )
    tier_filter
    return (tier_filter,)


@app.cell
def _(qa_df, tier_filter):
    if tier_filter.value == "all":
        filtered_df = qa_df
    else:
        filtered_df = qa_df[qa_df["tier"] == tier_filter.value]

    filtered_df[
        [
            "tier",
            "id",
            "question",
            "answer",
            "passage_count",
        ]
    ]
    return (filtered_df,)


@app.cell
def _(filtered_df, mo):
    row_choices = [
        f"{row.tier} #{row.id}: {row.question[:90]}"
        for row in filtered_df.itertuples(index=False)
    ]
    selected_row = mo.ui.dropdown(
        options=row_choices,
        value=row_choices[0],
        label="Inspect row",
    )
    selected_row
    return row_choices, selected_row


@app.cell
def _(filtered_df, merge_passage_spans, mo, row_choices, selected_row):
    row_index = row_choices.index(selected_row.value)
    sample = filtered_df.iloc[row_index]
    merged_passages = merge_passage_spans(sample["passages"])
    passages_md = "\n\n".join(
        f"**{passage['document_path']}** "
        f"`{passage['start_char']}:{passage['end_char']}`\n\n"
        f"{passage['content']}"
        for passage in merged_passages
    )
    sample_md = "\n\n".join(
        [
            f"## {sample['tier'].title()} #{sample['id']}",
            "**Question**",
            sample["question"],
            "**Answer**",
            sample["answer"],
            (
                f"**Passages** "
                f"(merged from {len(sample['passages'])} source spans)"
            ),
            passages_md,
        ]
    )

    mo.md(sample_md)
    return


if __name__ == "__main__":
    app.run()
