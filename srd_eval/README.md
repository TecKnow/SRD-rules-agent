# SRD Evaluation Baseline

This package implements the no-RAG baseline as two separate stages.

## Gather Answers

Set an OpenRouter key and provide one or more model IDs:

```powershell
$env:OPENROUTER_API_KEY = "..."
srd-eval-gather --model openai/gpt-4.1-mini --limit 3
```

The command writes immutable answer workbooks to `runs/no_rag/<run_id>/answers.jsonl`.
Use `--limit 3` for smoke tests and omit it for the full benchmark.

## Grade Answers

Grade a saved workbook with DeepEval:

```powershell
srd-eval-grade --answers runs/no_rag/<run_id>/answers.jsonl --limit 3
```

By default, the grader passes `--judge-model` to DeepEval's native model handling.
To use OpenRouter as the judge provider instead:

```powershell
srd-eval-grade --answers runs/no_rag/<run_id>/answers.jsonl --judge-provider openrouter --judge-model openai/gpt-4.1
```

Scores are written next to the answer workbook as `answers.deepeval_scores.jsonl`.
