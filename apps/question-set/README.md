# Question-set browser

Static marimo export target for the benchmark/question-set browser.

`scripts/build_question_set_public.py` refreshes this directory from the
repository-local source notebook and data files:

- `notebook.py` is copied from `ai-test-corpus-explore.py`
- `public/test-files/` is copied from `Resources/Test files/`
- `public/srd-markdown/` is copied from `data/source/downfallx-dnd-5e-srd-markdown/`

Rebuild from the repo root:

```powershell
$env:UV_CACHE_DIR='.uv-cache'; uv run python scripts\build_question_set_public.py
$env:UV_CACHE_DIR='.uv-cache'; uv run python -m marimo export html-wasm apps/question-set/notebook.py -o docs/question-set --mode run
```
