"""CLI to build/refresh a local SRD Chroma index for a chosen encoder.

Examples (run inside the WSL 3.13 agent venv, with Ollama/TEI serving the encoder):

    python -m srd_agent.build_index --encoder nomic --limit 50   # smoke build
    python -m srd_agent.build_index --encoder nomic               # full build
    python -m srd_agent.build_index --encoder bge-m3 --rebuild
"""

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .config import BGE_M3_TEI, DEFAULT_SRD_SOURCE_DIR, NOMIC_OLLAMA, NOMIC_OPENAI, AGENT_RUNS_DIR, EncoderSpec

# "nomic" matches the agent's default encoder (OpenAI-compatible endpoint) so the index
# the agent loads is the one this CLI builds. "nomic-native" uses Ollama's /api/embed.
ENCODERS: dict[str, EncoderSpec] = {
    "nomic": NOMIC_OPENAI,
    "nomic-native": NOMIC_OLLAMA,
    "bge-m3": BGE_M3_TEI,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a local SRD Chroma index for an encoder.")
    parser.add_argument("--encoder", choices=sorted(ENCODERS), default="nomic")
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SRD_SOURCE_DIR)
    parser.add_argument("--runs-dir", type=Path, default=AGENT_RUNS_DIR)
    parser.add_argument("--chunk-size", type=int, default=1200)
    parser.add_argument("--chunk-overlap", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--limit", type=int, default=None, help="Optional chunk limit for smoke builds.")
    parser.add_argument("--rebuild", action="store_true", help="Discard and re-embed even on a cache hit.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    from .index import prepare_index  # lazy: pulls chromadb

    _, manifest = prepare_index(
        ENCODERS[args.encoder],
        source_dir=args.source_dir,
        runs_dir=args.runs_dir,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        batch_size=args.batch_size,
        limit=args.limit,
        rebuild=args.rebuild,
    )
    print(json.dumps(asdict(manifest), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
