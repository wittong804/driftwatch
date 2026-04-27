"""Configuration loader for driftwatch CLI tool."""

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


DEFAULT_CONFIG_FILENAME = "driftwatch.toml"


@dataclass
class DatabaseConfig:
    url: str
    schema: Optional[str] = None


@dataclass
class DriftwatchConfig:
    database: DatabaseConfig
    models_path: str = "models"
    ignore_tables: list[str] = field(default_factory=list)
    strict: bool = False


def find_config_file(start_dir: Optional[Path] = None) -> Optional[Path]:
    """Walk up directories to find a driftwatch.toml config file."""
    current = Path(start_dir or Path.cwd()).resolve()
    for directory in [current, *current.parents]:
        candidate = directory / DEFAULT_CONFIG_FILENAME
        if candidate.exists():
            return candidate
    return None


def load_config(config_path: Optional[str] = None) -> DriftwatchConfig:
    """Load and parse the driftwatch configuration file."""
    if config_path:
        path = Path(config_path)
    else:
        path = find_config_file()

    if path is None or not path.exists():
        raise FileNotFoundError(
            f"No '{DEFAULT_CONFIG_FILENAME}' found. "
            "Run 'driftwatch init' or provide --config."
        )

    with open(path, "rb") as f:
        raw = tomllib.load(f)

    db_section = raw.get("database", {})
    if "url" not in db_section:
        raise ValueError("[database] url is required in config.")

    db_url = os.path.expandvars(db_section["url"])

    return DriftwatchConfig(
        database=DatabaseConfig(
            url=db_url,
            schema=db_section.get("schema"),
        ),
        models_path=raw.get("models_path", "models"),
        ignore_tables=raw.get("ignore_tables", []),
        strict=raw.get("strict", False),
    )
