"""The tool-using SRD agent: ChatOllama + search_srd, wired with LangGraph.

``create_react_agent`` gives the model a genuine tool loop (it decides when and how
often to call ``search_srd``) plus conversation memory via a checkpointer keyed by a
``thread_id`` (the conversation id). The agent is built once and reused; Ollama keeps
the model warm in VRAM.
"""

from dataclasses import dataclass
from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from .config import AgentConfig, GenSpec, load_agent_config
from .index import IndexManifest, prepare_index
from .retrieval import Retriever
from .tools import make_search_srd_tool

SYSTEM_PROMPT = """You are a D&D SRD 5.2.1 rules assistant.

Use the search_srd tool to ground every rules answer in the SRD 5.2.1 text. Call it
before answering, and call it again with a refined query if the retrieved passages do
not fully resolve the question.

Use only the retrieved SRD 5.2.1 context for rules facts. Do not import Pathfinder,
D&D 2014, forum rulings, or non-SRD 2024 material. When the retrieved context is
incomplete or ambiguous, say so plainly rather than guessing. Do not cite page numbers
or book sections; you may refer to the supplied source names when helpful. Keep answers
concise but complete enough to resolve the question."""


@dataclass(slots=True)
class AgentReply:
    answer: str
    citations: list[dict[str, Any]]
    tool_trace: list[dict[str, Any]]


@dataclass(slots=True)
class SrdAgent:
    graph: Any
    retriever: Retriever
    config: AgentConfig
    manifest: IndexManifest

    def ask(self, message: str, *, conversation_id: str = "default") -> AgentReply:
        run_config = {"configurable": {"thread_id": conversation_id}}
        result = self.graph.invoke({"messages": [{"role": "user", "content": message}]}, run_config)
        messages = result["messages"]
        answer = _message_text(messages[-1]) if messages else ""
        tool_trace, citations = _extract_trace(messages)
        return AgentReply(answer=answer, citations=citations, tool_trace=tool_trace)


def build_chat_model(gen: GenSpec):
    """Construct the chat model. ``openai`` (default) is portable to any OpenAI-compatible
    endpoint; ``ollama`` uses native ChatOllama. Both support tool calling."""
    if gen.backend == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=gen.model,
            base_url=gen.base_url,
            api_key=gen.api_key,
            temperature=gen.temperature,
        )
    if gen.backend == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=gen.model,
            base_url=gen.base_url.removesuffix("/v1"),
            temperature=gen.temperature,
            num_ctx=gen.num_ctx,
        )
    raise ValueError(f"Unknown generation backend: {gen.backend!r}")


def build_agent(config: AgentConfig | None = None) -> SrdAgent:
    """Build (and warm) the agent: loads/builds the index, then the LLM + tool loop."""
    config = config or load_agent_config()
    collection, manifest = prepare_index(
        config.retrieval.encoder,
        source_dir=config.source_dir,
        runs_dir=config.runs_dir,
        chunk_size=config.retrieval.chunk_size,
        chunk_overlap=config.retrieval.chunk_overlap,
    )
    retriever = Retriever.from_config(config.retrieval, collection)
    llm = build_chat_model(config.gen)
    graph = create_react_agent(
        llm,
        [make_search_srd_tool(retriever)],
        prompt=SYSTEM_PROMPT,
        checkpointer=MemorySaver(),
    )
    return SrdAgent(graph=graph, retriever=retriever, config=config, manifest=manifest)


def _message_text(message: Any) -> str:
    content = getattr(message, "content", message)
    if isinstance(content, list):  # some providers return content parts
        return "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in content)
    return str(content or "")


def _extract_trace(messages: list[Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Pull tool calls + citations out of the agent's message history."""
    tool_trace: list[dict[str, Any]] = []
    citations: list[dict[str, Any]] = []
    for message in messages:
        for call in getattr(message, "tool_calls", None) or []:
            tool_trace.append({"type": "call", "name": call.get("name"), "args": call.get("args")})
        if getattr(message, "type", None) == "tool" or message.__class__.__name__ == "ToolMessage":
            artifact = getattr(message, "artifact", None)
            tool_trace.append(
                {
                    "type": "result",
                    "name": getattr(message, "name", None),
                    "citations": artifact if isinstance(artifact, list) else [],
                }
            )
            if isinstance(artifact, list):
                citations.extend(artifact)
    return tool_trace, citations
