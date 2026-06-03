from pathlib import Path

from dotenv import load_dotenv

from .io import ROOT


def load_env(env_file: Path | None = None) -> None:
    load_dotenv(env_file or ROOT / ".env", override=False)
