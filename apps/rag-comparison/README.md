# RAG vs no-RAG answer browser

An interactive [marimo](https://marimo.io) notebook for browsing every model's
RAG and no-RAG answer to each SRD 5.2.1 benchmark question, side by side with the
judge's scores, rationales, error categories, and retrieved context. It is
exported to a static WebAssembly site and served from GitHub Pages — readers need
no install, and all computation runs in their browser.

## Files

| Path | Tracked? | What it is |
| --- | --- | --- |
| `notebook.py` | yes | The marimo notebook (source of truth) |
| `public/comparison_data.json` | **no** (gitignored) | Pre-baked dataset the notebook loads; regenerate with `srd-eval-build-wasm` |
| `_site/` | **no** (gitignored) | Scratch export dir, if used |
| `../../docs/` | yes | The exported WASM site served by GitHub Pages |

## Rebuild

Run from the repo root (uses the project venv):

```bash
# 1. Pre-bake the dataset from the no-RAG + RAG run artifacts.
#    Reuses the canonical merge logic in scripts/build_rag_comparison_report.py
#    so the numbers stay identical to reports/rag-vs-no-rag-performance.md.
srd-eval-build-wasm
# (equivalently: python scripts/build_wasm_dataset.py)

# 2. Export the notebook to the static WASM site that Pages serves.
marimo export html-wasm apps/rag-comparison/notebook.py -o docs --mode run
```

Step 1 writes `public/comparison_data.json`; step 2 copies that `public/` folder
into `docs/` alongside the exported `index.html`. To point at different runs, pass
`--no-rag-scores / --no-rag-answers / --rag-scores / --rag-answers / --benchmark`
to step 1 (defaults match the published report).

> Note: `public/comparison_data.json` is gitignored, so on a fresh clone run
> step 1 before opening the notebook with `marimo edit` or running step 2.

## Preview locally

```bash
# Edit/run the live notebook (needs public/comparison_data.json — run step 1 first):
marimo edit apps/rag-comparison/notebook.py

# Or serve the exported static site exactly as Pages will:
python -m http.server --directory docs
```

## Deploy (GitHub Pages)

The built site lives in `docs/`. In the repo's **Settings → Pages**, set the
source to **Deploy from a branch**, branch `main`, folder `/docs`. After pushing,
the browser is published at `https://<owner>.github.io/<repo>/`. A `.nojekyll`
file in `docs/` disables Jekyll so marimo's asset folders serve untouched.

To refresh after new runs: rerun the two rebuild steps, then commit `docs/`.
