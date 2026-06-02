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
    import json
    import re

    import marimo as mo
    import pandas as pd

    return Path, json, mo, pd, re


@app.cell
def _(mo):
    mo.md("""
    # AI-Generated SRD 5.2.1 Test Corpus Explorer

    Explore the repository-local silver benchmark built from AI-generated
    SRD 5.2.1 test-corpus reports. This notebook is read-only: it helps
    inspect row quality, likely failure modes, and source-grounding risks
    before model-answer collection begins.
    """)
    return


@app.cell
def _(Path):
    NOTEBOOK_DIR = Path(__file__).parent
    TEST_FILES_DIR = NOTEBOOK_DIR / "Resources" / "Test files"
    BENCHMARK_PATH = TEST_FILES_DIR / "benchmark.jsonl"
    QUESTIONS_PATH = TEST_FILES_DIR / "questions_only.jsonl"
    OUTPUTS_TEMPLATE_PATH = TEST_FILES_DIR / "model_outputs_template.jsonl"
    SRD_MARKDOWN_DIR = (
        NOTEBOOK_DIR / "data" / "source" / "downfallx-dnd-5e-srd-markdown"
    )
    return (
        BENCHMARK_PATH,
        OUTPUTS_TEMPLATE_PATH,
        QUESTIONS_PATH,
        SRD_MARKDOWN_DIR,
    )


@app.cell
def _(json, pd, re):
    FAILURE_MODE_COLUMNS = [
        "edition_drift",
        "pathfinder_or_other_system_bleed",
        "forum_or_unofficial_lore",
        "non_srd_2024_import",
        "partial_srd_retrieval",
        "overconfident_ambiguous_ruling",
        "source_scope_failure",
        "conversion_or_encoding_artifact",
        "unsupported_citation",
        "missed_limiting_phrase",
        "false_srd_exclusion",
        "rule_name_collision",
    ]

    QUALITY_COLUMNS = [
        "empty_expected_answer",
        "empty_rubric",
        "empty_srd_passages",
        "mojibake_marker",
        "rubric_heading_spillover",
        "stale_source_path",
    ]

    MOJIBAKE_MARKERS = ["â", "Ã", "î", "�", "\\u001a"]

    def read_jsonl(path):
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8-sig").splitlines()
            if line.strip()
        ]

    def compact_text(*parts):
        return " ".join(str(part or "") for part in parts).lower()

    def has_any(text, needles):
        return any(needle in text for needle in needles)

    def has_mojibake(text):
        return any(marker in str(text or "") for marker in MOJIBAKE_MARKERS)

    def make_failure_flags(row):
        text = compact_text(
            row.get("question"),
            row.get("expected_answer"),
            row.get("rubric"),
            row.get("alternative_interpretations"),
            row.get("common_wrong_answers"),
            row.get("failure_modes"),
            row.get("notes"),
            row.get("tags"),
            row.get("title"),
        )
        return {
            "edition_drift": has_any(
                text,
                [
                    "2014",
                    "5.1",
                    "legacy",
                    "old rule",
                    "older",
                    "previous edition",
                    "one d&d playtest",
                ],
            ),
            "pathfinder_or_other_system_bleed": has_any(
                text,
                [
                    "pathfinder",
                    "off-guard",
                    "touch ac",
                    "crit confirmation",
                    "3.5",
                    "other game",
                    "system bleed",
                ],
            ),
            "forum_or_unofficial_lore": has_any(
                text,
                [
                    "forum",
                    "community",
                    "designer tweet",
                    "designer tweets",
                    "rpg stack exchange",
                    "table ruling",
                    "most rulings",
                    "dm discretion",
                ],
            ),
            "non_srd_2024_import": has_any(
                text,
                [
                    "2024 phb",
                    "non-srd",
                    "outside srd",
                    "excluded",
                    "not in srd",
                    "player's handbook",
                    "player\u0027s handbook",
                ],
            ),
            "partial_srd_retrieval": has_any(
                text,
                [
                    "verify",
                    "unverified",
                    "chapter",
                    "elsewhere",
                    "specific text",
                    "only from",
                    "partial",
                    "source hierarchy",
                ],
            ),
            "overconfident_ambiguous_ruling": (
                row.get("answer_status") == "ambiguous"
                or row.get("contentiousness") == "high"
                or "do not choose a final table ruling" in text
            ),
            "source_scope_failure": has_any(
                text,
                [
                    "scope",
                    "outside srd",
                    "excluded",
                    "brand identity",
                    "licensing",
                    "not answerable",
                    "not present",
                ],
            ),
            "conversion_or_encoding_artifact": (
                has_mojibake(text)
                or "## category" in text
                or "# recommendations" in text
                or "onedrive" in str(row.get("source_file", "")).lower()
            ),
            "unsupported_citation": has_any(
                text,
                [
                    "unsupported citation",
                    "citation placeholders",
                    "sage advice",
                    "designer",
                    "faq",
                    "rpg stack exchange",
                    "without evidence",
                ],
            ),
            "missed_limiting_phrase": has_any(
                text,
                [
                    "while hidden",
                    "unless",
                    "except",
                    "immediately after",
                    "first time",
                    "once per turn",
                    "leaves your reach",
                    "doesn't expend",
                    "not included",
                    "limiting phrase",
                ],
            ),
            "false_srd_exclusion": has_any(
                text,
                [
                    "false srd exclusion",
                    "incorrectly claimed",
                    "not in srd",
                    "excluded from srd",
                    "absent from the srd",
                    "omitted",
                ],
            ),
            "rule_name_collision": has_any(
                text,
                [
                    "rule name collision",
                    "attack action",
                    "magic action",
                    "melee weapon attack",
                    "invisible condition",
                    "heroic inspiration",
                    "use an object",
                    "utilize",
                    "study action",
                    "search action",
                    "mysterious deck",
                    "deck of many things",
                    "off-guard",
                    "touch ac",
                ],
            ),
        }

    def make_quality_flags(row):
        row_text = " ".join(
            str(value or "") for value in row.to_dict().values()
        )
        return {
            "empty_expected_answer": not bool(row.get("expected_answer")),
            "empty_rubric": not bool(row.get("rubric")),
            "empty_srd_passages": not bool(row.get("srd_passages")),
            "mojibake_marker": has_mojibake(row_text),
            "rubric_heading_spillover": has_any(
                str(row.get("rubric", "")).lower(),
                ["## category", "# recommendations", "# caveats", "---"],
            ),
            "stale_source_path": "onedrive" in str(
                row.get("source_file", "")
            ).lower(),
        }

    def frame_from_rows(rows):
        frame = pd.DataFrame(rows)
        explicit_failure_columns = {
            column for column in FAILURE_MODE_COLUMNS if column in frame.columns
        }
        for column in FAILURE_MODE_COLUMNS + QUALITY_COLUMNS:
            if column not in frame.columns:
                frame[column] = False

        failure_rows = frame.apply(make_failure_flags, axis=1)
        quality_rows = frame.apply(make_quality_flags, axis=1)
        for column in FAILURE_MODE_COLUMNS:
            inferred_values = failure_rows.map(lambda flags: flags[column])
            if column in explicit_failure_columns:
                frame[column] = frame[column].fillna(inferred_values).astype(bool)
            else:
                frame[column] = inferred_values
        for column in QUALITY_COLUMNS:
            frame[column] = quality_rows.map(lambda flags: flags[column])

        frame["failure_mode_count"] = frame[FAILURE_MODE_COLUMNS].sum(axis=1)
        frame["quality_issue_count"] = frame[QUALITY_COLUMNS].sum(axis=1)
        frame["is_claude"] = frame["source_model"].eq("claude")
        return frame

    def boolean_summary(frame, columns):
        return (
            pd.DataFrame(
                {
                    "field": columns,
                    "rows": [int(frame[column].sum()) for column in columns],
                }
            )
            .sort_values("rows", ascending=False)
            .reset_index(drop=True)
        )

    def make_row_label(row):
        question = str(row.question)
        return f"{row.id} | {row.category} | {question[:100]}"

    def extract_search_terms(row, max_terms=8):
        text = " ".join(
            str(row.get(column, ""))
            for column in ["title", "question", "expected_answer", "tags"]
        )
        quoted_terms = re.findall(r'"([^"]{3,80})"', text)
        title_terms = re.split(r"[+/,()?:;\\-]+", str(row.get("title", "")))
        proper_terms = re.findall(
            r"\b[A-Z][A-Za-z']+(?:\s+[A-Z][A-Za-z']+){0,3}\b",
            text,
        )
        candidates = [*quoted_terms, *title_terms, *proper_terms]
        skipped = {
            "SRD",
            "D",
            "Q",
            "AI",
            "No",
            "Yes",
            "Full",
            "The",
            "Can",
            "Does",
        }
        terms = []
        for candidate in candidates:
            term = " ".join(candidate.strip().split())
            if len(term) < 4 or term in skipped:
                continue
            if term.lower() not in [existing.lower() for existing in terms]:
                terms.append(term)
            if len(terms) >= max_terms:
                break
        return terms

    def find_srd_snippets(row, srd_files, max_snippets=8):
        terms = extract_search_terms(row)
        snippets = []
        for term in terms:
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            for srd_file in srd_files:
                text = srd_file.read_text(encoding="utf-8")
                match = pattern.search(text)
                if not match:
                    continue
                start = max(0, match.start() - 240)
                end = min(len(text), match.end() + 360)
                snippet = text[start:end].strip()
                snippets.append(
                    {
                        "term": term,
                        "file": srd_file.name,
                        "snippet": snippet,
                    }
                )
                break
            if len(snippets) >= max_snippets:
                break
        return snippets

    def markdown_escape(text):
        return str(text or "").replace("\\", "\\\\")

    return (
        FAILURE_MODE_COLUMNS,
        QUALITY_COLUMNS,
        boolean_summary,
        frame_from_rows,
        find_srd_snippets,
        make_row_label,
        markdown_escape,
        read_jsonl,
    )


@app.cell
def _(
    BENCHMARK_PATH,
    OUTPUTS_TEMPLATE_PATH,
    QUESTIONS_PATH,
    frame_from_rows,
    pd,
    read_jsonl,
):
    benchmark_rows = read_jsonl(BENCHMARK_PATH)
    questions_rows = read_jsonl(QUESTIONS_PATH)
    outputs_template_rows = read_jsonl(OUTPUTS_TEMPLATE_PATH)

    benchmark_df = frame_from_rows(benchmark_rows)
    questions_df = pd.DataFrame(questions_rows)
    outputs_template_df = pd.DataFrame(outputs_template_rows)

    alignment_df = pd.DataFrame(
        {
            "check": [
                "benchmark rows",
                "questions rows",
                "model output template rows",
                "id order matches questions",
                "question text matches questions",
                "answer_status matches questions",
            ],
            "value": [
                len(benchmark_df),
                len(questions_df),
                len(outputs_template_df),
                benchmark_df["id"].tolist() == questions_df["id"].tolist(),
                benchmark_df["question"].tolist()
                == questions_df["question"].tolist(),
                benchmark_df["answer_status"].tolist()
                == questions_df["answer_status"].tolist(),
            ],
        }
    )
    return (
        alignment_df,
        benchmark_df,
        benchmark_rows,
        outputs_template_df,
        questions_df,
    )


@app.cell
def _(SRD_MARKDOWN_DIR):
    srd_files = sorted(SRD_MARKDOWN_DIR.glob("*.md"))
    return (srd_files,)


@app.cell
def _(alignment_df, benchmark_df, mo, srd_files):
    claude_rows = int(benchmark_df["source_model"].eq("claude").sum())
    verified_rows = int(
        benchmark_df["verification_status"].eq("verified_against_srd").sum()
    )
    gold_rows = int(benchmark_df["gold_dataset_linked"].fillna(False).sum())
    partial_rows = int(
        benchmark_df["verification_status"]
        .eq("partially_verified_against_srd")
        .sum()
    )
    ambiguous_rows = int(benchmark_df["answer_status"].eq("ambiguous").sum())
    curated_rows = int(benchmark_df["curation_status"].notna().sum())
    mo.md(f"""
    ## Corpus Snapshot

    Loaded **{len(benchmark_df):,}** benchmark rows, including
    **{claude_rows:,}** Claude rows. **{verified_rows:,}** rows are marked
    verified, **{partial_rows:,}** partially verified, and
    **{ambiguous_rows:,}** ambiguous. **{gold_rows:,}** rows are exact
    imports from the human-curated gold dataset. **{curated_rows:,}** rows
    have row-level curation metadata.

    Local SRD markdown files available for snippet search:
    **{len(srd_files):,}**.

    ### File Alignment
    """)
    alignment_df
    return


@app.cell
def _(benchmark_df):
    overview_df = (
        benchmark_df.groupby(
            [
                "source_model",
                "category",
                "answer_status",
                "verification_status",
                "curation_status",
                "gold_link_status",
            ],
            dropna=False,
        )
        .size()
        .reset_index(name="rows")
        .sort_values(["source_model", "category", "answer_status"])
    )
    overview_df
    return (overview_df,)


@app.cell
def _(FAILURE_MODE_COLUMNS, QUALITY_COLUMNS, benchmark_df, boolean_summary, mo):
    mo.md("## Failure-Mode and Data-Quality Signals")
    failure_mode_summary_df = boolean_summary(
        benchmark_df, FAILURE_MODE_COLUMNS
    )
    quality_summary_df = boolean_summary(benchmark_df, QUALITY_COLUMNS)
    return failure_mode_summary_df, quality_summary_df


@app.cell
def _(failure_mode_summary_df, mo, quality_summary_df):
    mo.hstack(
        [
            mo.vstack([mo.md("### Failure-Mode Tags"), failure_mode_summary_df]),
            mo.vstack([mo.md("### Data-Quality Flags"), quality_summary_df]),
        ]
    )
    return


@app.cell
def _(benchmark_df):
    dimension_summary_df = (
        benchmark_df.melt(
            id_vars=["id"],
            value_vars=[
                "source_model",
                "category",
                "difficulty",
                "contentiousness",
                "version_specificity",
                "answer_status",
                "verification_status",
                "curation_status",
                "gold_link_status",
            ],
            var_name="dimension",
            value_name="value",
        )
        .groupby(["dimension", "value"], dropna=False)
        .size()
        .reset_index(name="rows")
        .sort_values(["dimension", "rows"], ascending=[True, False])
    )
    dimension_summary_df
    return (dimension_summary_df,)


@app.cell
def _(benchmark_df, mo):
    source_filter = mo.ui.dropdown(
        options=["claude", "all", *sorted(benchmark_df["source_model"].unique())],
        value="claude",
        label="Source model",
    )
    verification_options = [
        "verified_or_partial",
        "all",
        *sorted(benchmark_df["verification_status"].dropna().unique()),
    ]
    verification_filter = mo.ui.dropdown(
        options=verification_options,
        value="verified_or_partial",
        label="Verification",
    )
    category_filter = mo.ui.dropdown(
        options=["all", *sorted(benchmark_df["category"].dropna().unique())],
        value="all",
        label="Category",
    )
    answer_status_filter = mo.ui.dropdown(
        options=[
            "all",
            *sorted(benchmark_df["answer_status"].dropna().unique()),
        ],
        value="all",
        label="Answer status",
    )
    mo.hstack(
        [
            source_filter,
            verification_filter,
            category_filter,
            answer_status_filter,
        ]
    )
    return (
        answer_status_filter,
        category_filter,
        source_filter,
        verification_filter,
    )


@app.cell
def _(
    answer_status_filter,
    benchmark_df,
    category_filter,
    source_filter,
    verification_filter,
):
    filtered_df = benchmark_df.copy()

    if source_filter.value != "all":
        filtered_df = filtered_df[
            filtered_df["source_model"].eq(source_filter.value)
        ]

    if verification_filter.value == "verified_or_partial":
        filtered_df = filtered_df[
            filtered_df["verification_status"].isin(
                ["verified_against_srd", "partially_verified_against_srd"]
                + ["verified_against_gold_dataset"]
            )
        ]
    elif verification_filter.value != "all":
        filtered_df = filtered_df[
            filtered_df["verification_status"].eq(verification_filter.value)
        ]

    if category_filter.value != "all":
        filtered_df = filtered_df[
            filtered_df["category"].eq(category_filter.value)
        ]

    if answer_status_filter.value != "all":
        filtered_df = filtered_df[
            filtered_df["answer_status"].eq(answer_status_filter.value)
        ]

    filtered_df = filtered_df.sort_values(
        ["is_claude", "verification_status", "source_id"],
        ascending=[False, True, True],
    )
    return (filtered_df,)


@app.cell
def _(filtered_df):
    filtered_table_df = filtered_df[
        [
            "id",
            "source_model",
            "category",
            "answer_status",
            "verification_status",
            "curation_status",
            "gold_link_status",
            "difficulty",
            "contentiousness",
            "version_specificity",
            "failure_mode_count",
            "quality_issue_count",
            "question",
        ]
    ]
    filtered_table_df
    return (filtered_table_df,)


@app.cell
def _(filtered_df, make_row_label, mo):
    row_choices = [make_row_label(row) for row in filtered_df.itertuples()]
    selected_row = mo.ui.dropdown(
        options=row_choices,
        value=row_choices[0],
        label="Inspect row",
    )
    selected_row
    return row_choices, selected_row


@app.cell
def _(filtered_df, row_choices, selected_row):
    selected_index = row_choices.index(selected_row.value)
    selected_row_data = filtered_df.iloc[selected_index].to_dict()
    return (selected_row_data,)


@app.cell
def _(
    FAILURE_MODE_COLUMNS,
    QUALITY_COLUMNS,
    markdown_escape,
    mo,
    selected_row_data,
):
    active_failure_modes = [
        column
        for column in FAILURE_MODE_COLUMNS
        if bool(selected_row_data.get(column))
    ]
    active_quality_flags = [
        column for column in QUALITY_COLUMNS if bool(selected_row_data.get(column))
    ]
    ambiguity_warning = (
        "\n\n> Ambiguous row: do not reward a final table ruling unless "
        "SRD 5.2.1 resolves it."
        if selected_row_data.get("answer_status") == "ambiguous"
        else ""
    )
    inspector_md = f"""
    ## {selected_row_data.get("id")} - {selected_row_data.get("title")}

    **Question**

    {markdown_escape(selected_row_data.get("question"))}

    **Expected answer**

    {markdown_escape(selected_row_data.get("expected_answer"))}

    **Rubric**

    {markdown_escape(selected_row_data.get("rubric"))}

    {ambiguity_warning}

    **Alternative interpretations**

    {markdown_escape(selected_row_data.get("alternative_interpretations"))}

    **Common wrong answers / failure modes**

    {markdown_escape(selected_row_data.get("common_wrong_answers"))}

    {markdown_escape(selected_row_data.get("failure_modes"))}

    **Notes**

    {markdown_escape(selected_row_data.get("notes"))}

    **Validation notes**

    {markdown_escape(selected_row_data.get("validation_notes"))}

    **Authority evidence**

    {markdown_escape(selected_row_data.get("authority_evidence"))}

    **Source**

    `{selected_row_data.get("source_model")}` /
    `{selected_row_data.get("source_id")}` /
    line `{selected_row_data.get("source_line")}`

    **Curation / verification**

    `{selected_row_data.get("curation_status")}` /
    `{selected_row_data.get("verification_status")}`

    **Gold dataset link**

    `{selected_row_data.get("gold_link_status")}` /
    `{selected_row_data.get("linked_gold_ids")}`

    **Active failure-mode tags**

    `{", ".join(active_failure_modes) or "none"}`

    **Active data-quality flags**

    `{", ".join(active_quality_flags) or "none"}`
    """
    mo.md(inspector_md)
    return active_failure_modes, active_quality_flags


@app.cell
def _(find_srd_snippets, selected_row_data, srd_files):
    srd_snippets = find_srd_snippets(selected_row_data, srd_files)
    return (srd_snippets,)


@app.cell
def _(mo, srd_snippets):
    snippets_md = "\n\n".join(
        "\n\n".join(
            [
                f"### `{snippet['term']}` in `{snippet['file']}`",
                snippet["snippet"],
            ]
        )
        for snippet in srd_snippets
    )
    mo.md(
        "## Likely Local SRD Snippets\n\n"
        + (
            snippets_md
            if snippets_md
            else "No snippet candidates found for this row."
        )
    )
    return


@app.cell
def _(json, mo, selected_row_data):
    row_for_prompt = {
        key: selected_row_data.get(key)
        for key in [
            "id",
            "question",
            "expected_answer",
            "rubric",
            "answer_status",
            "alternative_interpretations",
            "common_wrong_answers",
            "failure_modes",
            "notes",
            "validation_notes",
            "authority_evidence",
            "curation_status",
            "verification_status",
            "gold_dataset_linked",
            "gold_link_status",
            "linked_gold_ids",
            "gold_dataset_links",
        ]
    }
    row_json = json.dumps(row_for_prompt, indent=2, ensure_ascii=False)

    validation_prompt = f"""Validate this silver SRD 5.2.1 benchmark row against local SRD 5.2.1 text first. Use page-linked markdown before checking the PDF. Identify any incorrect expected-answer claims, missing caveats, non-SRD imports, unsupported citations, false SRD exclusions, or ambiguity that should be preserved. Return concise proposed edits, but do not rewrite unrelated fields.

Benchmark row:
{row_json}
"""
    taxonomy_prompt = f"""Classify the likely answer failure modes for this SRD 5.2.1 benchmark row. Use only these first-class labels: edition_drift, pathfinder_or_other_system_bleed, forum_or_unofficial_lore, non_srd_2024_import, partial_srd_retrieval, overconfident_ambiguous_ruling, source_scope_failure, conversion_or_encoding_artifact, unsupported_citation, missed_limiting_phrase, false_srd_exclusion, rule_name_collision. Explain why each selected label applies.

Benchmark row:
{row_json}
"""
    rewrite_prompt = f"""Rewrite this benchmark row's expected_answer and rubric as silver-quality grading material. Keep the question unchanged. Preserve ambiguity when SRD 5.2.1 does not resolve the issue. Penalize silent imports from D&D 2014, SRD 5.1, non-SRD 2024 PHB material, Pathfinder, forums, or partial SRD retrieval.

Benchmark row:
{row_json}
"""

    validation_area = mo.ui.text_area(
        value=validation_prompt,
        label="Validation prompt",
        full_width=True,
    )
    taxonomy_area = mo.ui.text_area(
        value=taxonomy_prompt,
        label="Failure-mode taxonomy prompt",
        full_width=True,
    )
    rewrite_area = mo.ui.text_area(
        value=rewrite_prompt,
        label="Silver-row rewrite prompt",
        full_width=True,
    )
    mo.vstack([validation_area, taxonomy_area, rewrite_area])
    return rewrite_area, taxonomy_area, validation_area


if __name__ == "__main__":
    app.run()
