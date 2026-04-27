"""Tests for driftwatch configuration loading."""

import pytest
from pathlib import Path
from unittest.mock import patch

from driftwatch.config import (
    load_config,
    find_config_file,
    DriftwatchConfig,
    DatabaseConfig,
    DEFAULT_CONFIG_FILENAME,
)


MINIMAL_TOML = b"""
[database]
url = "sqlite:///test.db"
"""

FULL_TOML = b"""
[database]
url = "postgresql://user:pass@localhost/mydb"
schema = "public"

models_path = "src/models"
ignore_tables = ["alembic_version"]
strict = true
"""


def test_load_minimal_config(tmp_path):
    config_file = tmp_path / DEFAULT_CONFIG_FILENAME
    config_file.write_bytes(MINIMAL_TOML)

    config = load_config(str(config_file))

    assert isinstance(config, DriftwatchConfig)
    assert config.database.url == "sqlite:///test.db"
    assert config.database.schema is None
    assert config.models_path == "models"
    assert config.ignore_tables == []
    assert config.strict is False


def test_load_full_config(tmp_path):
    config_file = tmp_path / DEFAULT_CONFIG_FILENAME
    config_file.write_bytes(FULL_TOML)

    config = load_config(str(config_file))

    assert config.database.url == "postgresql://user:pass@localhost/mydb"
    assert config.database.schema == "public"
    assert config.models_path == "src/models"
    assert config.ignore_tables == ["alembic_version"]
    assert config.strict is True


def test_missing_config_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="driftwatch.toml"):
        load_config(str(tmp_path / "nonexistent.toml"))


def test_missing_db_url_raises(tmp_path):
    config_file = tmp_path / DEFAULT_CONFIG_FILENAME
    config_file.write_bytes(b"[database]\n")

    with pytest.raises(ValueError, match="url is required"):
        load_config(str(config_file))


def test_find_config_file_walks_up(tmp_path):
    config_file = tmp_path / DEFAULT_CONFIG_FILENAME
    config_file.write_bytes(MINIMAL_TOML)
    nested = tmp_path / "a" / "b" / "c"
    nested.mkdir(parents=True)

    found = find_config_file(nested)
    assert found == config_file


def test_find_config_file_returns_none_when_missing(tmp_path):
    found = find_config_file(tmp_path / "no_config_here")
    assert found is None


def test_env_variable_expansion(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_URL", "sqlite:///env.db")
    config_file = tmp_path / DEFAULT_CONFIG_FILENAME
    config_file.write_bytes(b"[database]\nurl = \"${DB_URL}\"\n")

    config = load_config(str(config_file))
    assert config.database.url == "sqlite:///env.db"
