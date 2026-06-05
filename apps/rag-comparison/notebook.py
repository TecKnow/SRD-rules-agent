# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "pandas",
# ]
# ///

import marimo

__generated_with = "0.23.8"
app = marimo.App(width="full")


@app.cell
def _():
    import json

    import marimo as mo
    import pandas as pd

    return json, mo, pd


@app.cell
def _(mo):
    mo.md(
        """
        # SRD RAG vs no-RAG answer browser

        Every model answered each D&D SRD 5.2.1 benchmark question **twice** — once
        with retrieved SRD context (**RAG**) and once from its own knowledge
        (**no-RAG**) — and an LLM judge scored both. Use the filters to find pairs of
        interest, then select a row to read the two answers and their judgements side
        by side.
        """
    )
    return


@app.cell
def _(json, mo):
    # In WASM the notebook is served over HTTP and `notebook_location()` is a URL;
    # locally it is the notebook directory. Handle both so the same file works in
    # `marimo edit` and in the exported static site.
    import urllib.request

    _ref = mo.notebook_location() / "public" / "comparison_data.json"
    _url = str(_ref)
    if _url.startswith("http"):
        with urllib.request.urlopen(_url) as _resp:  # noqa: S310 - same-origin asset
            data = json.loads(_resp.read().decode("utf-8"))
    else:
        with open(_url, encoding="utf-8") as _handle:
            data = json.load(_handle)

    pairs = data["pairs"]
    chunks = data["chunks"]
    summary = data["summary"]
    meta = data["meta"]
    failure_types = meta["failure_types"]
    pairs_by_key = {(row["question_id"], row["model"]): row for row in pairs}
    return chunks, failure_types, meta, pairs, pairs_by_key, summary


@app.cell
def _(meta, mo, summary):
    mo.md(
        f"""
        **{summary["paired_count"]} matched pairs** &nbsp; · &nbsp;
        avg score **{summary["average_no_rag_score"]:.3f} → {summary["average_rag_score"]:.3f}**
        ({summary["average_score_delta"]:+.3f}) &nbsp; · &nbsp;
        passes **{summary["no_rag_pass_count"]} → {summary["rag_pass_count"]}** &nbsp; · &nbsp;
        RAG improved **{summary["improved"]}** / declined **{summary["declined"]}** / unchanged **{summary["unchanged"]}**

        <sub>Judge: {meta["evaluator_version"]} · sources: {meta["sources"]["no_rag_scores"]} vs {meta["sources"]["rag_scores"]}</sub>
        """
    )
    return


@app.cell
def _(failure_types, mo, pairs):
    def _options(field):
        values = {str(row.get(field, "")) for row in pairs if str(row.get(field, "")).strip()}
        return ["All"] + sorted(values)

    model_filter = mo.ui.dropdown(_options("model"), value="All", label="Model")
    source_filter = mo.ui.dropdown(_options("source_model"), value="All", label="Question source")
    category_filter = mo.ui.dropdown(_options("category"), value="All", label="Category")
    difficulty_filter = mo.ui.dropdown(_options("difficulty"), value="All", label="Difficulty")
    contentiousness_filter = mo.ui.dropdown(_options("contentiousness"), value="All", label="Contentiousness")
    version_filter = mo.ui.dropdown(_options("version_specificity"), value="All", label="Version specificity")

    swing_preset = mo.ui.dropdown(
        [
            "All swings",
            "RAG improved (Δ > 0)",
            "RAG declined (Δ < 0)",
            "Big swings (|Δ| ≥ 0.5)",
            "Custom range (use slider)",
        ],
        value="All swings",
        label="Score swing",
    )
    swing_slider = mo.ui.range_slider(
        start=-1.0,
        stop=1.0,
        step=0.05,
        value=[-1.0, 1.0],
        label="Custom Δ range",
        show_value=True,
    )

    failure_type_filter = mo.ui.dropdown(["All"] + list(failure_types), value="All", label="Error category")
    failure_where_filter = mo.ui.dropdown(
        [
            "Any side",
            "Present in no-RAG",
            "Present in RAG",
            "New in RAG",
            "Resolved by RAG",
            "Changed either way",
        ],
        value="Any side",
        label="Error applies to",
    )
    question_filter = mo.ui.text(value="", label="Question text / ID contains", full_width=True)

    mo.vstack(
        [
            mo.hstack([model_filter, source_filter, category_filter], justify="start", gap=1),
            mo.hstack([difficulty_filter, contentiousness_filter, version_filter], justify="start", gap=1),
            mo.hstack([swing_preset, swing_slider], justify="start", gap=1),
            mo.hstack([failure_type_filter, failure_where_filter], justify="start", gap=1),
            question_filter,
        ],
        gap=0.75,
    )
    return (
        category_filter,
        contentiousness_filter,
        difficulty_filter,
        failure_type_filter,
        failure_where_filter,
        model_filter,
        question_filter,
        source_filter,
        swing_preset,
        swing_slider,
        version_filter,
    )


@app.cell
def _(
    category_filter,
    contentiousness_filter,
    difficulty_filter,
    failure_type_filter,
    failure_where_filter,
    model_filter,
    pairs,
    question_filter,
    source_filter,
    swing_preset,
    swing_slider,
    version_filter,
):
    def _categorical_match(row):
        for field, control in (
            ("model", model_filter),
            ("source_model", source_filter),
            ("category", category_filter),
            ("difficulty", difficulty_filter),
            ("contentiousness", contentiousness_filter),
            ("version_specificity", version_filter),
        ):
            if control.value != "All" and str(row.get(field, "")) != control.value:
                return False
        return True

    def _swing_match(row):
        delta = row["score_delta"]
        preset = swing_preset.value
        if preset == "RAG improved (Δ > 0)":
            return delta > 0
        if preset == "RAG declined (Δ < 0)":
            return delta < 0
        if preset == "Big swings (|Δ| ≥ 0.5)":
            return abs(delta) >= 0.5
        if preset == "Custom range (use slider)":
            low, high = swing_slider.value
            return low <= delta <= high
        return True

    def _failure_match(row):
        failure_type = failure_type_filter.value
        if failure_type == "All":
            return True
        no_rag_active = set(row["resolved_failure_types"]) | set(row["shared_failure_types"])
        rag_active = set(row["new_failure_types"]) | set(row["shared_failure_types"])
        where = failure_where_filter.value
        if where == "Present in no-RAG":
            return failure_type in no_rag_active
        if where == "Present in RAG":
            return failure_type in rag_active
        if where == "New in RAG":
            return failure_type in row["new_failure_types"]
        if where == "Resolved by RAG":
            return failure_type in row["resolved_failure_types"]
        if where == "Changed either way":
            return failure_type in row["changed_failure_types"]
        return failure_type in (no_rag_active | rag_active)

    def _text_match(row):
        needle = question_filter.value.strip().lower()
        if not needle:
            return True
        return needle in row["question_id"].lower() or needle in row["question"].lower()

    filtered = [
        row
        for row in pairs
        if _categorical_match(row) and _swing_match(row) and _failure_match(row) and _text_match(row)
    ]
    filtered = sorted(filtered, key=lambda row: row["abs_score_delta"], reverse=True)
    return (filtered,)


@app.cell
def _(filtered, mo, pd):
    browse_df = pd.DataFrame(
        [
            {
                "question_id": row["question_id"],
                "model": row["model"],
                "source": row.get("source_model", ""),
                "category": row["category"],
                "difficulty": row["difficulty"],
                "no_rag": round(row["no_rag_score"], 2),
                "rag": round(row["rag_score"], 2),
                "Δ": round(row["score_delta"], 2),
                "transition": row["pass_transition"],
                "rag_errors": row["rag_failure_count"],
                "top_source_file": row["top_source_file"],
            }
            for row in filtered
        ]
    )

    if browse_df.empty:
        browse_table = mo.ui.table(browse_df, selection=None, label="No matching pairs")
        _view = mo.md("**No pairs match the current filters.** Loosen a filter above.")
    else:
        browse_table = mo.ui.table(
            browse_df,
            selection="single",
            page_size=20,
            label=f"{len(filtered)} matched pairs — sorted by |Δ| desc; click a row to inspect",
        )
        _view = browse_table

    _view
    return (browse_table,)


@app.cell
def _(browse_table, filtered, pairs_by_key):
    _selection = browse_table.value
    selected_pair = None
    try:
        if _selection is not None and len(_selection) > 0:
            _row = _selection.iloc[0] if hasattr(_selection, "iloc") else _selection[0]
            selected_pair = pairs_by_key.get((_row["question_id"], _row["model"]))
    except (KeyError, IndexError, TypeError):
        selected_pair = None
    # Fall back to the top filtered pair so the detail panel is never empty.
    if selected_pair is None and filtered:
        selected_pair = filtered[0]
    return (selected_pair,)


@app.cell
def _(mo, selected_pair):
    if selected_pair is None:
        _detail_header = mo.md("Select a pair above to read the answers and judgements.")
    else:
        _p = selected_pair
        _detail_header = mo.md(
            f"""
            ## {_p["question_id"]} &nbsp;·&nbsp; `{_p["model"]}`

            | | no-RAG | RAG |
            | --- | --- | --- |
            | **Score** | {_p["no_rag_score"]:.2f} | {_p["rag_score"]:.2f} (Δ {_p["score_delta"]:+.2f}) |
            | **Pass** | {"✅" if _p["no_rag_passed"] else "❌"} | {"✅" if _p["rag_passed"] else "❌"} |
            | **Judged errors** | {_p["no_rag_failure_count"]} | {_p["rag_failure_count"]} |

            **Source:** {_p.get("source_model", "")} &nbsp;·&nbsp; **Category:** {_p["category"]} &nbsp;·&nbsp;
            **Difficulty:** {_p["difficulty"]} &nbsp;·&nbsp; **Answer status:** {_p["answer_status"]}

            ### Question

            {_p["question"]}
            """
        )
    _detail_header
    return


@app.cell
def _(mo, selected_pair):
    _no_rag_answer = selected_pair.get("no_rag_answer", "") if selected_pair else ""
    _rag_answer = selected_pair.get("rag_answer", "") if selected_pair else ""
    mo.hstack(
        [
            mo.ui.text_area(value=_no_rag_answer, rows=20, label="No-RAG answer", disabled=True, full_width=True),
            mo.ui.text_area(value=_rag_answer, rows=20, label="RAG answer", disabled=True, full_width=True),
        ],
        widths="equal",
        gap=1,
    )
    return


@app.cell
def _(mo, selected_pair):
    _no_rag_rationale = selected_pair.get("no_rag_rationale", "") if selected_pair else ""
    _rag_rationale = selected_pair.get("rag_rationale", "") if selected_pair else ""
    mo.hstack(
        [
            mo.ui.text_area(value=_no_rag_rationale, rows=8, label="No-RAG judge rationale", disabled=True, full_width=True),
            mo.ui.text_area(value=_rag_rationale, rows=8, label="RAG judge rationale", disabled=True, full_width=True),
        ],
        widths="equal",
        gap=1,
    )
    return


@app.cell
def _(failure_types, mo, pd, selected_pair):
    if selected_pair is None:
        _failure_view = mo.md("")
    else:
        _no_rag_active = set(selected_pair["resolved_failure_types"]) | set(selected_pair["shared_failure_types"])
        _rag_active = set(selected_pair["new_failure_types"]) | set(selected_pair["shared_failure_types"])
        _no_rag_notes = selected_pair.get("no_rag_failure_notes", {})
        _rag_notes = selected_pair.get("rag_failure_notes", {})
        _rows = []
        for _failure_type in failure_types:
            _in_no_rag = _failure_type in _no_rag_active
            _in_rag = _failure_type in _rag_active
            if not (_in_no_rag or _in_rag):
                continue
            _rows.append(
                {
                    "error category": _failure_type,
                    "no-RAG": "•" if _in_no_rag else "",
                    "RAG": "•" if _in_rag else "",
                    "change": "resolved by RAG" if (_in_no_rag and not _in_rag) else ("new in RAG" if (_in_rag and not _in_no_rag) else "both"),
                    "no-RAG note": _no_rag_notes.get(_failure_type, ""),
                    "RAG note": _rag_notes.get(_failure_type, ""),
                }
            )
        if _rows:
            _failure_view = mo.vstack(
                [mo.md("### Judged error categories"), mo.ui.table(pd.DataFrame(_rows), selection=None, page_size=10)]
            )
        else:
            _failure_view = mo.md("### Judged error categories\n\nNeither answer was flagged with any error category.")
    _failure_view
    return


@app.cell
def _(chunks, mo, pd, selected_pair):
    if selected_pair is None:
        _context_view = mo.md("")
    else:
        _rows = []
        for _ref in selected_pair.get("retrieved_context", []):
            _chunk = chunks.get(_ref["chunk_id"], {})
            _chunk_meta = _chunk.get("metadata", {})
            _rows.append(
                {
                    "rank": _ref.get("rank"),
                    "distance": _ref.get("distance"),
                    "source_file": _chunk_meta.get("source_file", ""),
                    "name": _chunk_meta.get("name", ""),
                    "entity_type": _chunk_meta.get("entity_type", ""),
                    "h1": _chunk_meta.get("h1", ""),
                    "h2": _chunk_meta.get("h2", ""),
                    "chunk_id": _ref["chunk_id"],
                }
            )
        _heading = mo.md(
            "### RAG retrieved context\n\nThe SRD chunks fed to the model for its RAG answer, "
            "ordered by retrieval rank (lower distance = closer vector match)."
        )
        if _rows:
            _context_view = mo.vstack([_heading, mo.ui.table(pd.DataFrame(_rows), selection=None, page_size=10)])
        else:
            _context_view = mo.vstack([_heading, mo.md("_No retrieved context recorded for this answer._")])
    _context_view
    return


@app.cell
def _(chunks, mo, selected_pair):
    _refs = selected_pair.get("retrieved_context", []) if selected_pair else []
    _options = [
        f"{_ref.get('rank')}: {chunks.get(_ref['chunk_id'], {}).get('metadata', {}).get('name', _ref['chunk_id'])}"
        f" (distance {_ref.get('distance')})"
        for _ref in _refs
    ]
    chunk_picker = mo.ui.dropdown(
        _options or ["No retrieved context"],
        value=(_options[0] if _options else "No retrieved context"),
        label="Inspect a retrieved chunk",
        full_width=True,
    )
    chunk_picker
    return (chunk_picker,)


@app.cell
def _(chunk_picker, chunks, json, mo, selected_pair):
    _refs = selected_pair.get("retrieved_context", []) if selected_pair else []
    _options = [
        f"{_ref.get('rank')}: {chunks.get(_ref['chunk_id'], {}).get('metadata', {}).get('name', _ref['chunk_id'])}"
        f" (distance {_ref.get('distance')})"
        for _ref in _refs
    ]
    if _refs and chunk_picker.value in _options:
        _ref = _refs[_options.index(chunk_picker.value)]
        _chunk = chunks.get(_ref["chunk_id"], {})
        _chunk_view = mo.vstack(
            [
                mo.ui.text_area(
                    value=_chunk.get("text", ""),
                    rows=14,
                    label="Retrieved chunk text",
                    disabled=True,
                    full_width=True,
                ),
                mo.ui.text_area(
                    value=json.dumps(_chunk.get("metadata", {}), ensure_ascii=False, indent=2, sort_keys=True),
                    rows=8,
                    label="Chunk metadata",
                    disabled=True,
                    full_width=True,
                ),
            ]
        )
    else:
        _chunk_view = mo.md("")
    _chunk_view
    return


if __name__ == "__main__":
    app.run()
