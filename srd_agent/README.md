# SRD 5.2.1 Rules Agent (local, offline, tool-using)

An interactive agent that answers D&D SRD 5.2.1 rules questions, grounded in the SRD
text via retrieval. It is the product layer on top of the research pipeline
(`srd_eval` / `srd_rag`): a LangGraph tool-using agent served over a local FastAPI
service, with all models running locally on the GPU.

- **Generation:** an **OpenAI-compatible** backend (`ChatOpenAI`), defaulting to a local
  **Ollama** `/v1` endpoint running `qwen2.5:7b-instruct`. Swap to LM Studio, vLLM, a shared
  local server, or a hosted API by setting `OPENAI_BASE_URL` / `OPENAI_API_KEY` — no code change.
- **One service by default:** the same local endpoint serves both chat and the `nomic-embed-text`
  encoder, so a basic setup is just **Ollama + this app**. The reranker is **optional and off by
  default** (it would add a second service or a torch dependency).
- **Retrieval:** pluggable **encoder → Chroma → cross-encoder reranker** (`retrieval.py`),
  selected by `config.RetrievalConfig`. The reranker (and any encoder/serving change) is chosen
  by the **bake-off** on measured score.
- **Agent:** `create_react_agent` — a genuine tool loop; the model decides when to call
  `search_srd` and can search multiple times per question. Conversation memory per
  `conversation_id`.

## Runtime

The agent is pure-Python HTTP clients (no torch), and all of its compiled dependencies
(`chromadb`, `pydantic`, `onnxruntime`, `tokenizers`, …) run on **Python 3.14**, so the
simplest setup is the repo's **native Windows 3.14** environment — one venv, no WSL:

```powershell
# From the repo root, into the project venv (or a sibling):
uv pip install -r requirements-agent.txt
```

WSL/Docker is only needed if you later adopt a **TEI/Infinity reranker server** or the
**in-process sentence-transformers** reranker (which pulls CUDA torch). The default
no-reranker setup needs neither.

## 1. Start the model server

```powershell
# Ollama serves both the generation LLM and the nomic encoder over one OpenAI-compatible API.
ollama serve                  # or run it as a background service
ollama pull qwen2.5:7b-instruct
ollama pull nomic-embed-text
```

> VRAM: Qwen-7B adds ~5 GB on top of desktop GPU usage. Close GPU-heavy GUI apps
> (browsers, Electron apps, games) if the 4080 is tight.

## 2. Build the local index

Chunks the SRD markdown (reusing `srd_rag.embed_srd.chunk_corpus`) and embeds it into a
signature-keyed Chroma collection under `runs/agent/<signature>/`. Idempotent — a second
run with unchanged inputs is a cache hit.

```bash
python -m srd_agent.build_index --encoder nomic --limit 50   # smoke
python -m srd_agent.build_index --encoder nomic              # full
```

## 3. (Optional) Run the retrieval bake-off

Pick the encoder/reranker combo by measured judged score on the 180-question benchmark.
Needs `OPENROUTER_API_KEY` in `.env` (the judge is the existing OpenRouter-backed grader).

```bash
python -m srd_agent.bakeoff --candidate nomic-none --limit 20            # smoke (Ollama only)
python -m srd_agent.bakeoff --candidate nomic-none --candidate nomic-bge  # needs TEI for nomic-bge
```

Prints a ranked table and writes `runs/agent/bakeoff/summary.json`. Set the winner as the
default in `config.py` (or via `SRD_AGENT_RERANK_MODEL` / `SRD_AGENT_TEI_RERANK_URL`).

## 4. Run the agent service

```bash
uvicorn srd_agent.server:app --host 127.0.0.1 --port 8000
```

- Open <http://127.0.0.1:8000/> for the chat UI.
- Health: `curl http://127.0.0.1:8000/health`
- Ask:

```bash
curl -s http://127.0.0.1:8000/chat -H 'content-type: application/json' \
  -d '{"message": "What is the new name for \"Use an Object\"?", "conversation_id": "demo"}' | jq
```

The response includes `answer`, `citations` (the SRD passages the tool returned), and
`tool_trace` (the search calls the agent made). `POST /chat/stream` is an SSE variant that
streams token deltas then a final `done` event.

## Configuration (env, all optional)

| Variable | Default | Purpose |
| --- | --- | --- |
| `OPENAI_BASE_URL` | `http://127.0.0.1:11434/v1` | OpenAI-compatible endpoint (chat + embeddings) |
| `OPENAI_API_KEY` | `ollama` | ignored by local servers; set for a hosted API |
| `SRD_AGENT_GEN_MODEL` | `qwen2.5:7b-instruct` | generation model id |
| `SRD_AGENT_GEN_BACKEND` | `openai` | `openai` (any /v1) or `ollama` (native) |
| `SRD_AGENT_EMBED_BASE_URL` | _(= `OPENAI_BASE_URL`)_ | embeddings endpoint if different from chat |
| `SRD_AGENT_RERANK_MODEL` | _(unset → no reranker)_ | TEI reranker model id |
| `SRD_AGENT_TEI_RERANK_URL` | `http://127.0.0.1:8081` | TEI rerank server |
| `SRD_AGENT_TOP_K` / `SRD_AGENT_FETCH_K` | `6` / `30` | passages kept / candidates fetched |

## Layout

| File | Role |
| --- | --- |
| `config.py` | env-overridable config; encoder/reranker/retrieval specs as data |
| `retrieval.py` | `Encoder` + `Reranker` protocols, impls, and `Retriever.search` |
| `index.py` / `build_index.py` | signature-keyed Chroma index build/load + CLI |
| `tools.py` | `search_srd` tool (returns formatted passages + citation artifact) |
| `agent.py` | `ChatOllama` + `create_react_agent` tool loop + memory |
| `server.py` / `web/index.html` | FastAPI service + thin chat UI |
| `bakeoff.py` | retrieval candidate comparison via the existing judge |
