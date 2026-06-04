from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
import sys
from textwrap import shorten
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from srd_eval.grade_deepeval import FAILURE_TYPES
from srd_eval.io import ROOT, JsonObject, read_jsonl


NO_RAG_RUN_DIR = ROOT / "runs" / "no_rag" / "no-rag-20260603T074521Z-07aa8696"
RAG_RUN_DIR = ROOT / "runs" / "rag" / "rag-chroma-20260604-full"

NO_RAG_SCORES_PATH = NO_RAG_RUN_DIR / "answers_for_grading.deepeval_scores.success_only.jsonl"
NO_RAG_ANSWERS_PATH = NO_RAG_RUN_DIR / "answers_for_grading.jsonl"
RAG_SCORES_PATH = RAG_RUN_DIR / "answers.deepeval_scores.jsonl"
RAG_ANSWERS_PATH = RAG_RUN_DIR / "answers.jsonl"

REPORT_DIR = ROOT / "reports"
FIGURES_DIR = REPORT_DIR / "figures"
REPORT_PATH = REPORT_DIR / "rag-vs-no-rag-performance.md"

GREEN = "#3d7f5f"
RED = "#ad5b53"
BLUE = "#4c6f9f"
GOLD = "#c6953b"
GRAY = "#6f6f6f"


def pair_key(row: JsonObject) -> tuple[str, str]:
    return str(row.get("question_id")), str(row.get("model"))


def full_key(row: JsonObject) -> tuple[str, str, str]:
    return str(row.get("run_id")), str(row.get("question_id")), str(row.get("model"))


def sorted_retrieved_contexts(row: JsonObject) -> list[JsonObject]:
    rag_payload = row.get("rag", {})
    contexts = rag_payload.get("retrieved_context", []) if isinstance(rag_payload, dict) else []
    if not isinstance(contexts, list):
        return []
    return sorted(
        [context for context in contexts if isinstance(context, dict)],
        key=lambda context: int(context.get("rank", 10**9)),
    )


def merge_score_records(
    *,
    score_records: list[JsonObject],
    answer_records: list[JsonObject],
    answer_set: str,
) -> tuple[list[JsonObject], list[JsonObject]]:
    answers_by_full_key = {full_key(row): row for row in answer_records}
    answers_by_pair_key = {pair_key(row): row for row in answer_records}
    error_rows = [row for row in score_records if row.get("error")]
    scored_rows = [row for row in score_records if not row.get("error") and "score" in row]

    merged_rows = []
    for score_row in sorted(scored_rows, key=lambda row: int(row.get("answer_index", 10**9))):
        answer_row = answers_by_full_key.get(full_key(score_row), answers_by_pair_key.get(pair_key(score_row), {}))
        metadata = score_row.get("question_metadata") or answer_row.get("benchmark_metadata", {})
        failure_types = score_row.get("failure_types", {})
        active_failures = [
            failure_type
            for failure_type in FAILURE_TYPES
            if isinstance(failure_types, dict) and failure_types.get(failure_type)
        ]
        contexts = sorted_retrieved_contexts(answer_row)
        distances = [
            float(context["distance"])
            for context in contexts
            if context.get("distance") is not None
        ]
        top_context = contexts[0] if contexts else {}
        top_metadata = top_context.get("metadata", {}) if isinstance(top_context.get("metadata", {}), dict) else {}
        merged_rows.append(
            {
                **score_row,
                "answer_set": answer_set,
                "question": answer_row.get("question", ""),
                "answer": answer_row.get("answer", ""),
                "category": metadata.get("category", ""),
                "difficulty": metadata.get("difficulty", ""),
                "answer_status": metadata.get("answer_status", ""),
                "active_failure_types": active_failures,
                "active_failure_types_text": ", ".join(active_failures),
                "failure_count": len(active_failures),
                "retrieved_context_count": len(contexts),
                "top_distance": distances[0] if distances else None,
                "avg_distance": sum(distances) / len(distances) if distances else None,
                "top_source_file": top_metadata.get("source_file", ""),
                "top_source_name": top_metadata.get("name", ""),
                "top_chunk_id": top_context.get("chunk_id", ""),
            }
        )
    return merged_rows, error_rows


def build_pair_records(no_rag_records: list[JsonObject], rag_records: list[JsonObject]) -> tuple[list[JsonObject], int, int]:
    no_rag_by_key = {pair_key(row): row for row in no_rag_records}
    rag_by_key = {pair_key(row): row for row in rag_records}
    shared_keys = sorted(set(no_rag_by_key) & set(rag_by_key))
    no_rag_only_count = len(set(no_rag_by_key) - set(rag_by_key))
    rag_only_count = len(set(rag_by_key) - set(no_rag_by_key))

    pair_records = []
    for key in shared_keys:
        no_rag_row = no_rag_by_key[key]
        rag_row = rag_by_key[key]
        no_rag_failures = set(no_rag_row["active_failure_types"])
        rag_failures = set(rag_row["active_failure_types"])
        score_delta = float(rag_row["score"]) - float(no_rag_row["score"])
        pair_records.append(
            {
                "question_id": key[0],
                "model": key[1],
                "question": rag_row.get("question") or no_rag_row.get("question", ""),
                "category": rag_row.get("category") or no_rag_row.get("category", ""),
                "difficulty": rag_row.get("difficulty") or no_rag_row.get("difficulty", ""),
                "answer_status": rag_row.get("answer_status") or no_rag_row.get("answer_status", ""),
                "no_rag_score": float(no_rag_row["score"]),
                "rag_score": float(rag_row["score"]),
                "score_delta": score_delta,
                "abs_score_delta": abs(score_delta),
                "no_rag_passed": bool(no_rag_row["passed"]),
                "rag_passed": bool(rag_row["passed"]),
                "pass_transition": f"{'pass' if no_rag_row['passed'] else 'fail'} -> {'pass' if rag_row['passed'] else 'fail'}",
                "no_rag_failure_count": int(no_rag_row["failure_count"]),
                "rag_failure_count": int(rag_row["failure_count"]),
                "failure_count_delta": int(rag_row["failure_count"]) - int(no_rag_row["failure_count"]),
                "new_failure_types": sorted(rag_failures - no_rag_failures),
                "resolved_failure_types": sorted(no_rag_failures - rag_failures),
                "shared_failure_types": sorted(no_rag_failures & rag_failures),
                "changed_failure_types": sorted(no_rag_failures ^ rag_failures),
                "no_rag_answer": no_rag_row.get("answer", ""),
                "rag_answer": rag_row.get("answer", ""),
                "no_rag_rationale": no_rag_row.get("rationale", ""),
                "rag_rationale": rag_row.get("rationale", ""),
                "top_source_file": rag_row.get("top_source_file", ""),
                "top_source_name": rag_row.get("top_source_name", ""),
                "top_distance": rag_row.get("top_distance"),
                "avg_distance": rag_row.get("avg_distance"),
            }
        )
    return pair_records, no_rag_only_count, rag_only_count


def percent(value: float) -> str:
    return f"{value:.1%}"


def fmt_num(value: Any, digits: int = 3, signed: bool = False) -> str:
    if value is None or pd.isna(value):
        return ""
    sign = "+" if signed else ""
    return f"{float(value):{sign}.{digits}f}"


def markdown_table(rows: Iterable[dict[str, Any]], columns: list[tuple[str, str]]) -> str:
    rows = list(rows)
    headers = [header for header, _ in columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        cells = []
        for _, key in columns:
            value = row.get(key, "")
            if isinstance(value, list):
                value = ", ".join(str(item) for item in value)
            text = str(value).replace("\n", " ").replace("|", "\\|")
            cells.append(text)
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def save_model_delta_chart(model_df: pd.DataFrame) -> str:
    path = FIGURES_DIR / "model-average-score-delta.png"
    plot_df = model_df.sort_values("avg_score_delta", ascending=True)
    fig, ax = plt.subplots(figsize=(9, 4.8))
    colors = [GREEN if value >= 0 else RED for value in plot_df["avg_score_delta"]]
    ax.barh(plot_df["model"], plot_df["avg_score_delta"], color=colors)
    ax.axvline(0, color="#333333", linewidth=1)
    ax.set_title("Average score delta by model")
    ax.set_xlabel("RAG score minus no-RAG score")
    ax.set_ylabel("")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return str(path.relative_to(REPORT_DIR)).replace("\\", "/")


def save_pass_counts_chart(model_df: pd.DataFrame) -> str:
    path = FIGURES_DIR / "model-pass-counts.png"
    plot_df = model_df.sort_values("rag_passes", ascending=True)
    y_positions = range(len(plot_df))
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.barh([position - 0.18 for position in y_positions], plot_df["no_rag_passes"], height=0.34, label="No-RAG", color=GRAY)
    ax.barh([position + 0.18 for position in y_positions], plot_df["rag_passes"], height=0.34, label="RAG", color=GREEN)
    ax.set_yticks(list(y_positions), plot_df["model"])
    ax.set_title("Pass counts by model")
    ax.set_xlabel("Passed rows out of 180")
    ax.set_ylabel("")
    ax.grid(axis="x", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return str(path.relative_to(REPORT_DIR)).replace("\\", "/")


def save_direction_chart(model_df: pd.DataFrame) -> str:
    path = FIGURES_DIR / "model-score-delta-direction.png"
    plot_df = model_df.sort_values("avg_score_delta", ascending=True)
    fig, ax = plt.subplots(figsize=(9, 4.8))
    left = pd.Series([0] * len(plot_df), index=plot_df.index, dtype=float)
    for column, label, color in [
        ("declined", "Declined", RED),
        ("unchanged", "Unchanged", GRAY),
        ("improved", "Improved", GREEN),
    ]:
        ax.barh(plot_df["model"], plot_df[column], left=left, label=label, color=color)
        left += plot_df[column]
    ax.set_title("Score movement by model")
    ax.set_xlabel("Matched question/model pairs")
    ax.set_ylabel("")
    ax.grid(axis="x", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return str(path.relative_to(REPORT_DIR)).replace("\\", "/")


def save_failure_delta_chart(failure_df: pd.DataFrame) -> str:
    path = FIGURES_DIR / "failure-type-count-delta.png"
    plot_df = failure_df.sort_values("count_delta", ascending=True)
    fig, ax = plt.subplots(figsize=(9, 5.2))
    colors = [GREEN if value <= 0 else RED for value in plot_df["count_delta"]]
    ax.barh(plot_df["failure_type"], plot_df["count_delta"], color=colors)
    ax.axvline(0, color="#333333", linewidth=1)
    ax.set_title("Failure type count delta")
    ax.set_xlabel("RAG count minus no-RAG count")
    ax.set_ylabel("")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return str(path.relative_to(REPORT_DIR)).replace("\\", "/")


def save_heatmap(df: pd.DataFrame, *, value_column: str, index: str, columns: str, title: str, filename: str) -> str:
    path = FIGURES_DIR / filename
    pivot = df.pivot_table(values=value_column, index=index, columns=columns, aggfunc="mean").sort_index()
    fig_width = max(7.5, 1.3 * len(pivot.columns) + 2.8)
    fig_height = max(4.8, 0.48 * len(pivot.index) + 1.8)
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    image = ax.imshow(pivot.values, cmap="RdYlGn", aspect="auto", vmin=-0.35, vmax=0.35)
    ax.set_xticks(range(len(pivot.columns)), pivot.columns, rotation=30, ha="right")
    ax.set_yticks(range(len(pivot.index)), pivot.index)
    ax.set_title(title)
    for row_index in range(len(pivot.index)):
        for column_index in range(len(pivot.columns)):
            value = pivot.iloc[row_index, column_index]
            if pd.notna(value):
                ax.text(column_index, row_index, f"{value:+.2f}", ha="center", va="center", fontsize=8)
    fig.colorbar(image, ax=ax, label="Average RAG minus no-RAG score")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return str(path.relative_to(REPORT_DIR)).replace("\\", "/")


def save_retrieval_scatter(df: pd.DataFrame) -> str:
    path = FIGURES_DIR / "retrieval-distance-vs-score-delta.png"
    plot_df = df.dropna(subset=["top_distance", "score_delta"])
    fig, ax = plt.subplots(figsize=(8, 5))
    for model, model_rows in plot_df.groupby("model"):
        ax.scatter(model_rows["top_distance"], model_rows["score_delta"], label=model, alpha=0.65, s=22)
    ax.axhline(0, color="#333333", linewidth=1)
    ax.set_title("RAG top retrieval distance vs score delta")
    ax.set_xlabel("Top retrieved chunk distance")
    ax.set_ylabel("RAG score minus no-RAG score")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return str(path.relative_to(REPORT_DIR)).replace("\\", "/")


def top_examples(df: pd.DataFrame, *, ascending: bool, limit: int = 8) -> list[dict[str, Any]]:
    rows = []
    for row in df.sort_values(["score_delta", "question_id", "model"], ascending=[ascending, True, True]).head(limit).to_dict("records"):
        direction = "Improved" if row["score_delta"] > 0 else "Regressed"
        resolved = row["resolved_failure_types"]
        new = row["new_failure_types"]
        if resolved and not new:
            interpretation = f"{direction}; RAG resolved {', '.join(resolved[:3])}."
        elif new and not resolved:
            interpretation = f"{direction}; RAG introduced {', '.join(new[:3])}."
        elif resolved and new:
            interpretation = f"{direction}; resolved {', '.join(resolved[:2])}, introduced {', '.join(new[:2])}."
        else:
            interpretation = f"{direction}; score changed without a failure-type change."
        rows.append(
            {
                "question_id": row["question_id"],
                "model": row["model"],
                "no_rag_score": fmt_num(row["no_rag_score"], 2),
                "rag_score": fmt_num(row["rag_score"], 2),
                "delta": fmt_num(row["score_delta"], 2, signed=True),
                "failure_change": interpretation,
                "question": shorten(str(row["question"]), width=110, placeholder="..."),
            }
        )
    return rows


def source_rows(df: pd.DataFrame) -> list[dict[str, Any]]:
    grouped = (
        df.groupby("top_source_file", dropna=False)
        .agg(
            pairs=("question_id", "count"),
            avg_score_delta=("score_delta", "mean"),
            avg_top_distance=("top_distance", "mean"),
            improved=("score_delta", lambda values: int((values > 0).sum())),
            declined=("score_delta", lambda values: int((values < 0).sum())),
        )
        .reset_index()
        .sort_values(["pairs", "avg_score_delta"], ascending=[False, False])
        .head(12)
    )
    rows = []
    for row in grouped.to_dict("records"):
        rows.append(
            {
                "top_source_file": row["top_source_file"] or "(missing)",
                "pairs": int(row["pairs"]),
                "avg_score_delta": fmt_num(row["avg_score_delta"], signed=True),
                "avg_top_distance": fmt_num(row["avg_top_distance"]),
                "improved": int(row["improved"]),
                "declined": int(row["declined"]),
            }
        )
    return rows


def distance_bin_rows(df: pd.DataFrame) -> list[dict[str, Any]]:
    plot_df = df.dropna(subset=["top_distance"]).copy()
    plot_df["distance_bin"] = pd.cut(
        plot_df["top_distance"],
        bins=[0, 0.45, 0.50, 0.55, 0.60, 1.0],
        labels=["<=0.45", "0.45-0.50", "0.50-0.55", "0.55-0.60", ">0.60"],
        include_lowest=True,
    )
    grouped = (
        plot_df.groupby("distance_bin", observed=False)
        .agg(
            pairs=("question_id", "count"),
            avg_score_delta=("score_delta", "mean"),
            improved=("score_delta", lambda values: int((values > 0).sum())),
            declined=("score_delta", lambda values: int((values < 0).sum())),
        )
        .reset_index()
    )
    return [
        {
            "distance_bin": str(row["distance_bin"]),
            "pairs": int(row["pairs"]),
            "avg_score_delta": fmt_num(row["avg_score_delta"], signed=True),
            "improved": int(row["improved"]),
            "declined": int(row["declined"]),
        }
        for row in grouped.to_dict("records")
        if int(row["pairs"]) > 0
    ]


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    no_rag_scores = list(read_jsonl(NO_RAG_SCORES_PATH))
    no_rag_answers = list(read_jsonl(NO_RAG_ANSWERS_PATH))
    rag_scores = list(read_jsonl(RAG_SCORES_PATH))
    rag_answers = list(read_jsonl(RAG_ANSWERS_PATH))

    no_rag_records, no_rag_error_rows = merge_score_records(
        score_records=no_rag_scores,
        answer_records=no_rag_answers,
        answer_set="no_rag",
    )
    rag_records, rag_error_rows = merge_score_records(
        score_records=rag_scores,
        answer_records=rag_answers,
        answer_set="rag",
    )
    pair_records, no_rag_only_count, rag_only_count = build_pair_records(no_rag_records, rag_records)
    comparison_df = pd.DataFrame(pair_records)

    if comparison_df.empty:
        raise ValueError("No matched no-RAG/RAG pairs were found.")

    paired_count = len(comparison_df)
    no_rag_pass_count = int(comparison_df["no_rag_passed"].sum())
    rag_pass_count = int(comparison_df["rag_passed"].sum())
    improved_count = int((comparison_df["score_delta"] > 0).sum())
    declined_count = int((comparison_df["score_delta"] < 0).sum())
    unchanged_count = paired_count - improved_count - declined_count
    average_no_rag_score = float(comparison_df["no_rag_score"].mean())
    average_rag_score = float(comparison_df["rag_score"].mean())
    average_score_delta = float(comparison_df["score_delta"].mean())

    model_df = (
        comparison_df.groupby("model", dropna=False)
        .agg(
            pairs=("question_id", "count"),
            no_rag_avg_score=("no_rag_score", "mean"),
            rag_avg_score=("rag_score", "mean"),
            avg_score_delta=("score_delta", "mean"),
            no_rag_passes=("no_rag_passed", "sum"),
            rag_passes=("rag_passed", "sum"),
            improved=("score_delta", lambda values: int((values > 0).sum())),
            unchanged=("score_delta", lambda values: int((values == 0).sum())),
            declined=("score_delta", lambda values: int((values < 0).sum())),
        )
        .reset_index()
    )
    model_df["pass_delta"] = model_df["rag_passes"] - model_df["no_rag_passes"]
    model_df = model_df.sort_values(["avg_score_delta", "model"], ascending=[False, True])

    model_table_rows = []
    for row in model_df.to_dict("records"):
        model_table_rows.append(
            {
                "model": row["model"],
                "pairs": int(row["pairs"]),
                "no_rag_avg_score": fmt_num(row["no_rag_avg_score"]),
                "rag_avg_score": fmt_num(row["rag_avg_score"]),
                "avg_score_delta": fmt_num(row["avg_score_delta"], signed=True),
                "no_rag_passes": int(row["no_rag_passes"]),
                "rag_passes": int(row["rag_passes"]),
                "pass_delta": f"{int(row['pass_delta']):+d}",
                "improved": int(row["improved"]),
                "unchanged": int(row["unchanged"]),
                "declined": int(row["declined"]),
            }
        )

    failure_rows = []
    for failure_type in FAILURE_TYPES:
        no_rag_count = sum(failure_type in row["active_failure_types"] for row in no_rag_records)
        rag_count = sum(failure_type in row["active_failure_types"] for row in rag_records)
        new_count = sum(failure_type in row["new_failure_types"] for row in pair_records)
        resolved_count = sum(failure_type in row["resolved_failure_types"] for row in pair_records)
        failure_rows.append(
            {
                "failure_type": failure_type,
                "no_rag_count": int(no_rag_count),
                "rag_count": int(rag_count),
                "count_delta": int(rag_count - no_rag_count),
                "resolved_by_rag": int(resolved_count),
                "new_in_rag": int(new_count),
            }
        )
    failure_df = pd.DataFrame(failure_rows).sort_values(["count_delta", "failure_type"], ascending=[True, True])
    failure_table_rows = [
        {
            "failure_type": row["failure_type"],
            "no_rag_count": int(row["no_rag_count"]),
            "rag_count": int(row["rag_count"]),
            "count_delta": f"{int(row['count_delta']):+d}",
            "resolved_by_rag": int(row["resolved_by_rag"]),
            "new_in_rag": int(row["new_in_rag"]),
        }
        for row in failure_df.to_dict("records")
    ]

    def grouped_table(column: str) -> list[dict[str, Any]]:
        grouped = (
            comparison_df.groupby(column, dropna=False)
            .agg(
                pairs=("question_id", "count"),
                no_rag_avg_score=("no_rag_score", "mean"),
                rag_avg_score=("rag_score", "mean"),
                avg_score_delta=("score_delta", "mean"),
                no_rag_passes=("no_rag_passed", "sum"),
                rag_passes=("rag_passed", "sum"),
            )
            .reset_index()
            .sort_values(["avg_score_delta", column], ascending=[False, True])
        )
        grouped["pass_delta"] = grouped["rag_passes"] - grouped["no_rag_passes"]
        return [
            {
                column: row[column] or "(blank)",
                "pairs": int(row["pairs"]),
                "no_rag_avg_score": fmt_num(row["no_rag_avg_score"]),
                "rag_avg_score": fmt_num(row["rag_avg_score"]),
                "avg_score_delta": fmt_num(row["avg_score_delta"], signed=True),
                "pass_delta": f"{int(row['pass_delta']):+d}",
            }
            for row in grouped.to_dict("records")
        ]

    model_delta_chart = save_model_delta_chart(model_df)
    pass_counts_chart = save_pass_counts_chart(model_df)
    direction_chart = save_direction_chart(model_df)
    failure_delta_chart = save_failure_delta_chart(failure_df)
    difficulty_heatmap = save_heatmap(
        comparison_df,
        value_column="score_delta",
        index="model",
        columns="difficulty",
        title="Average score delta by model and difficulty",
        filename="model-difficulty-score-delta-heatmap.png",
    )
    category_heatmap = save_heatmap(
        comparison_df,
        value_column="score_delta",
        index="model",
        columns="category",
        title="Average score delta by model and category",
        filename="model-category-score-delta-heatmap.png",
    )
    retrieval_scatter = save_retrieval_scatter(comparison_df)

    best_model = model_df.iloc[0]
    weakest_model = model_df.sort_values(["avg_score_delta", "model"], ascending=[True, True]).iloc[0]
    largest_failure_reduction = failure_df.iloc[0]
    largest_failure_increase = failure_df.sort_values(["count_delta", "failure_type"], ascending=[False, True]).iloc[0]

    report = f"""# RAG vs No-RAG Performance Report

Generated by `scripts/build_rag_comparison_report.py`.

## Executive Summary

This report compares the preserved no-RAG run against the full Chroma RAG run using matched `(question_id, model)` pairs only. The comparison includes {paired_count} matched pairs across {model_df["model"].nunique()} models, with {len(no_rag_error_rows)} no-RAG score errors and {len(rag_error_rows)} RAG score errors skipped.

Overall, RAG raised the average judged score from {average_no_rag_score:.3f} to {average_rag_score:.3f}, an average delta of {average_score_delta:+.3f}. Passes increased from {no_rag_pass_count} to {rag_pass_count}, a change of {rag_pass_count - no_rag_pass_count:+d} paired rows. At the row level, RAG improved {improved_count} pairs, declined on {declined_count}, and left {unchanged_count} unchanged.

The biggest model-level lift was `{best_model["model"]}` at {float(best_model["avg_score_delta"]):+.3f} average score delta. The smallest lift was `{weakest_model["model"]}` at {float(weakest_model["avg_score_delta"]):+.3f}. RAG most reduced `{largest_failure_reduction["failure_type"]}` ({int(largest_failure_reduction["count_delta"]):+d} rows), while `{largest_failure_increase["failure_type"]}` increased the most ({int(largest_failure_increase["count_delta"]):+d} rows).

Coverage checks: no-RAG score rows = {len(no_rag_scores)}, RAG score rows = {len(rag_scores)}, unmatched no-RAG pairs = {no_rag_only_count}, unmatched RAG pairs = {rag_only_count}.

## Model-Level Performance

![Average score delta by model]({model_delta_chart})

![Pass counts by model]({pass_counts_chart})

![Score movement by model]({direction_chart})

{markdown_table(
        model_table_rows,
        [
            ("Model", "model"),
            ("Pairs", "pairs"),
            ("No-RAG Avg", "no_rag_avg_score"),
            ("RAG Avg", "rag_avg_score"),
            ("Avg Delta", "avg_score_delta"),
            ("No-RAG Pass", "no_rag_passes"),
            ("RAG Pass", "rag_passes"),
            ("Pass Delta", "pass_delta"),
            ("Improved", "improved"),
            ("Unchanged", "unchanged"),
            ("Declined", "declined"),
        ],
    )}

## Failure-Type Shifts

Negative deltas are good in this table: they mean RAG produced fewer judged failures of that type than no-RAG.

![Failure type count delta]({failure_delta_chart})

{markdown_table(
        failure_table_rows,
        [
            ("Failure Type", "failure_type"),
            ("No-RAG Count", "no_rag_count"),
            ("RAG Count", "rag_count"),
            ("Delta", "count_delta"),
            ("Resolved by RAG", "resolved_by_rag"),
            ("New in RAG", "new_in_rag"),
        ],
    )}

## Benchmark Slices

The difficulty and category views show where RAG changed performance most. Positive values mean RAG improved the average score for that slice.

![Score delta by model and difficulty]({difficulty_heatmap})

![Score delta by model and category]({category_heatmap})

### Difficulty

{markdown_table(
        grouped_table("difficulty"),
        [
            ("Difficulty", "difficulty"),
            ("Pairs", "pairs"),
            ("No-RAG Avg", "no_rag_avg_score"),
            ("RAG Avg", "rag_avg_score"),
            ("Avg Delta", "avg_score_delta"),
            ("Pass Delta", "pass_delta"),
        ],
    )}

### Category

{markdown_table(
        grouped_table("category"),
        [
            ("Category", "category"),
            ("Pairs", "pairs"),
            ("No-RAG Avg", "no_rag_avg_score"),
            ("RAG Avg", "rag_avg_score"),
            ("Avg Delta", "avg_score_delta"),
            ("Pass Delta", "pass_delta"),
        ],
    )}

### Answer Status

{markdown_table(
        grouped_table("answer_status"),
        [
            ("Answer Status", "answer_status"),
            ("Pairs", "pairs"),
            ("No-RAG Avg", "no_rag_avg_score"),
            ("RAG Avg", "rag_avg_score"),
            ("Avg Delta", "avg_score_delta"),
            ("Pass Delta", "pass_delta"),
        ],
    )}

## Retrieval Quality

The RAG run records the top retrieved context and Chroma distance for each answer. Lower distance generally means a closer vector match, but this is not a direct correctness score. The scatter plot is useful for spotting whether regressions cluster around weaker retrieval.

![Retrieval distance vs score delta]({retrieval_scatter})

### Top Retrieved Source Files

{markdown_table(
        source_rows(comparison_df),
        [
            ("Top Source File", "top_source_file"),
            ("Pairs", "pairs"),
            ("Avg Delta", "avg_score_delta"),
            ("Avg Top Distance", "avg_top_distance"),
            ("Improved", "improved"),
            ("Declined", "declined"),
        ],
    )}

### Distance Bins

{markdown_table(
        distance_bin_rows(comparison_df),
        [
            ("Top Distance Bin", "distance_bin"),
            ("Pairs", "pairs"),
            ("Avg Delta", "avg_score_delta"),
            ("Improved", "improved"),
            ("Declined", "declined"),
        ],
    )}

## Largest Wins and Regressions

### Largest RAG Wins

{markdown_table(
        top_examples(comparison_df, ascending=False),
        [
            ("Question ID", "question_id"),
            ("Model", "model"),
            ("No-RAG", "no_rag_score"),
            ("RAG", "rag_score"),
            ("Delta", "delta"),
            ("Failure Change", "failure_change"),
            ("Question", "question"),
        ],
    )}

### Largest RAG Regressions

{markdown_table(
        top_examples(comparison_df, ascending=True),
        [
            ("Question ID", "question_id"),
            ("Model", "model"),
            ("No-RAG", "no_rag_score"),
            ("RAG", "rag_score"),
            ("Delta", "delta"),
            ("Failure Change", "failure_change"),
            ("Question", "question"),
        ],
    )}

## Notes

- Primary metric: DeepEval judged score and threshold pass/fail.
- Pairing key: `(question_id, model)`.
- No-RAG artifact: `{NO_RAG_SCORES_PATH.relative_to(ROOT).as_posix()}`.
- RAG artifact: `{RAG_SCORES_PATH.relative_to(ROOT).as_posix()}`.
- RAG retrieval artifact: `{RAG_ANSWERS_PATH.relative_to(ROOT).as_posix()}`.
"""
    REPORT_PATH.write_text(report, encoding="utf-8", newline="\n")
    print(f"Wrote {REPORT_PATH}")
    print(f"Wrote figures to {FIGURES_DIR}")


if __name__ == "__main__":
    main()
