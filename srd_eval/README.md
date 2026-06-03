# SRD Evaluation Baseline

This package implements the no-RAG baseline as two separate stages.

## Gather Answers

Copy `.env.sample` to `.env`, then fill in the API keys and model defaults you need.
The commands load `.env` automatically and never override variables already set in your shell.

Gather with the models listed in `OPENROUTER_MODELS`:

```powershell
srd-eval-gather --limit 3
```

The command writes immutable answer workbooks to `runs/no_rag/<run_id>/answers.jsonl`.
Use `--limit 3` for smoke tests and omit it for the full benchmark.
You can still pass `--model` one or more times to override `OPENROUTER_MODELS`.

For an overnight full run:

```powershell
uv run srd-eval-gather
```

The gather command prints one progress line for each question/model request and appends each answer record to JSONL immediately. If a run is interrupted, resume it with the printed run id:

```powershell
uv run srd-eval-gather --run-id <run_id> --resume
```

By default, request failures are recorded and the run stops so you can fix the cause, such as an exhausted API budget. After fixing the issue, rerun with `--resume`; completed question/model pairs are skipped and failed pairs are retried. Use `--continue-on-error` only when you want the run to keep going after individual request failures.

## Grade Answers

Grade a saved workbook with DeepEval:

```powershell
srd-eval-grade --answers runs/no_rag/<run_id>/answers.jsonl --limit 3
```

By default, the grader passes `--judge-model` to DeepEval's native model handling.
Set `DEEPEVAL_JUDGE_PROVIDER=openrouter` in `.env` to use OpenRouter as the default judge provider, or pass it explicitly:

```powershell
srd-eval-grade --answers runs/no_rag/<run_id>/answers.jsonl --judge-provider openrouter --judge-model openai/gpt-4.1
```

Scores are written next to the answer workbook as `answers.deepeval_scores.jsonl`.

## Preserved Baseline Run

The repository includes a completed no-RAG baseline workbook for analysis and presentation:

```text
runs/no_rag/no-rag-20260603T074521Z-07aa8696/answers_for_grading.jsonl
```

This file contains 900 successful answer records: 180 benchmark questions across 5 OpenRouter models. It is the cleaned grading input derived from the completed run, with a transient duplicate/error row removed.

## LangChain Demo

Open `langchain-answer-gathering-demo.py` to see the same gathering shape through LangChain's `ChatOpenRouter` integration:

```powershell
uv run marimo edit langchain-answer-gathering-demo.py
```

The notebook uses `.env`, loads the local benchmark, and produces workbook-style records.
If `OPENROUTER_MODELS` is unset, the notebook defaults to `openrouter/owl-alpha` for an easy first demo.
When run as a script, it uses dry-run placeholder answers so checks do not spend API calls.

## Supported Environment Variables

- `OPENROUTER_API_KEY`: required for answer gathering and OpenRouter-backed judging.
- `OPENROUTER_MODELS`: optional comma-separated default gather models.
- `OPENROUTER_SITE_URL`: optional OpenRouter referer metadata.
- `DEEPEVAL_JUDGE_PROVIDER`: `openrouter` or `deepeval`; defaults to `deepeval` if unset.
- `DEEPEVAL_JUDGE_MODEL`: default judge model; defaults to `gpt-4.1` if unset.
- `OPENAI_API_KEY`: needed only for native DeepEval/OpenAI judging.
