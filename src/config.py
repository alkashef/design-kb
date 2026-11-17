"""Read the settings of the app from config/.env and the environment (D-24).

This is the only module that reads config/.env or the environment. A real environment variable
overrides the value in config/.env. docs/design.md, section "Settings", explains each key.
"""

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / "config" / ".env"


@dataclass(frozen=True)
class Settings:
    """Holds the settings of the app, one field for each key of config/.env.example."""

    host: str
    port: int
    data_dir: str
    ollama_url: str
    embedding_model: str
    embedding_timeout_seconds: float
    search_result_limit: int
    page_size: int


def read_env_file(path: Path) -> dict[str, str]:
    """Return the KEY=value pairs of a .env file. Skip empty lines and comments."""
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _value(values: dict[str, str], key: str) -> str:
    """Return the value of a key, from the environment first, then from the .env values."""
    value = os.environ.get(key, values.get(key))
    if value is None or value == "":
        raise RuntimeError(f"The setting {key} is missing. Add it to {ENV_FILE}.")
    return value


def load_settings(path: Path = ENV_FILE) -> Settings:
    """Read the settings from the .env file at path and from the environment."""
    values = read_env_file(path)
    return Settings(
        host=_value(values, "HOST"),
        port=int(_value(values, "PORT")),
        data_dir=str(ROOT / _value(values, "DATA_DIR")),
        ollama_url=_value(values, "OLLAMA_URL"),
        embedding_model=_value(values, "EMBEDDING_MODEL"),
        embedding_timeout_seconds=float(_value(values, "EMBEDDING_TIMEOUT_SECONDS")),
        search_result_limit=int(_value(values, "SEARCH_RESULT_LIMIT")),
        page_size=int(_value(values, "PAGE_SIZE")),
    )
