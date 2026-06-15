"""Local, offline, tool-using SRD 5.2.1 rules agent.

This package is the interactive product layer that sits on top of the research
pipeline (``srd_eval`` / ``srd_rag``). It serves a LangGraph tool-using agent over
a local FastAPI service, with the generation LLM served by Ollama and a pluggable
encoder -> Chroma -> reranker retrieval pipeline.

The package runs in a separate WSL2 + Python 3.13 environment (see
``requirements-agent.txt``); the repo's 3.14 Windows venv stays for marimo/eval.
"""
