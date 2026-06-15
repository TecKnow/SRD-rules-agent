"""Local FastAPI service for the SRD rules agent.

The agent (LLM + index + tool loop) is built once at startup and reused across
requests, so Ollama keeps the model warm in VRAM. Run inside the WSL agent venv:

    uvicorn srd_agent.server:app --host 127.0.0.1 --port 8000

Endpoints:
    GET  /health        liveness + model/index status
    POST /chat          {message, conversation_id} -> {answer, citations, tool_trace}
    POST /chat/stream    server-sent events: token deltas then a final `done` event
    GET  /              thin chat UI
"""

import asyncio
import json
import queue
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from .agent import SrdAgent, build_agent

WEB_DIR = Path(__file__).resolve().parent / "web"


class ChatRequest(BaseModel):
    message: str
    conversation_id: str = "default"


class ChatResponse(BaseModel):
    answer: str
    citations: list[dict[str, Any]]
    tool_trace: list[dict[str, Any]]
    conversation_id: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.agent = await run_in_threadpool(build_agent)
    yield


app = FastAPI(title="SRD 5.2.1 Rules Agent", lifespan=lifespan)


def _agent(app: FastAPI) -> SrdAgent:
    return app.state.agent


@app.get("/health")
async def health() -> dict[str, Any]:
    agent: SrdAgent = _agent(app)
    gen = agent.config.gen
    # Backend-agnostic reachability: /v1/models for openai-compatible, /api/tags for native ollama.
    probe = f"{gen.base_url.rstrip('/')}/models" if gen.backend == "openai" else f"{gen.base_url.rstrip('/')}/api/tags"
    backend_ok = False
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(probe, headers={"Authorization": f"Bearer {gen.api_key}"})
            backend_ok = resp.status_code == 200
    except Exception:
        backend_ok = False
    return {
        "status": "ok" if backend_ok else "degraded",
        "backend": gen.backend,
        "backend_reachable": backend_ok,
        "gen_model": gen.model,
        "retrieval": agent.config.retrieval.id,
        "index_chunks": agent.manifest.chunk_count,
        "collection": agent.manifest.collection_name,
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    agent: SrdAgent = _agent(app)
    reply = await run_in_threadpool(agent.ask, request.message, conversation_id=request.conversation_id)
    return ChatResponse(
        answer=reply.answer,
        citations=reply.citations,
        tool_trace=reply.tool_trace,
        conversation_id=request.conversation_id,
    )


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    agent: SrdAgent = _agent(app)
    events: queue.Queue[dict[str, Any] | None] = queue.Queue()

    def worker() -> None:
        run_config = {"configurable": {"thread_id": request.conversation_id}}
        try:
            for chunk, metadata in agent.graph.stream(
                {"messages": [{"role": "user", "content": request.message}]},
                run_config,
                stream_mode="messages",
            ):
                # Only stream assistant text from the agent node (skip tool nodes).
                if metadata.get("langgraph_node") == "agent":
                    text = getattr(chunk, "content", "")
                    if isinstance(text, str) and text:
                        events.put({"type": "token", "text": text})
            state = agent.graph.get_state(run_config)
            messages = state.values.get("messages", []) if state else []
            from .agent import _extract_trace

            tool_trace, citations = _extract_trace(messages)
            events.put({"type": "done", "citations": citations, "tool_trace": tool_trace})
        except Exception as exc:  # surface errors to the client stream
            events.put({"type": "error", "message": str(exc)})
        finally:
            events.put(None)

    threading.Thread(target=worker, daemon=True).start()

    async def event_source():
        loop = asyncio.get_running_loop()
        while True:
            event = await loop.run_in_executor(None, events.get)
            if event is None:
                break
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_source(), media_type="text/event-stream")


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")
