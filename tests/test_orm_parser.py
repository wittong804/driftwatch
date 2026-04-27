"""Tests for driftwatch.orm_parser module."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from driftwatch.introspect import TableSchema
from driftwatch.orm_parser import extract_orm_schemas


MODELS_CONTENT = textwrap.dedent("""
    from sqlalchemy import Column, Integer, String, Boolean
    from sqlalchemy.orm import DeclarativeBase

    class Base(DeclarativeBase):
        pass

    class Product(Base):
        __tablename__ = "products"
        id = Column(Integer, primary_key=True)
        title = Column(String(255), nullable=False)
        active = Column(Boolean, nullable=True)

    class Order(Base):
        __tablename__ = "orders"
        id = Column(Integer, primary_key=True)
        product_id = Column(Integer, nullable=False)
""")


@pytest.fixture()
def models_file(tmp_path) -> Path:
    path = tmp_path / "models.py"
    path.write_text(MODELS_CONTENT)
    return path


def test_extract_returns_dict(models_file):
    schemas = extract_orm_schemas(str(models_file))
    assert isinstance(schemas, dict)


def test_extract_finds_all_tables(models_file):
    schemas = extract_orm_schemas(str(models_file))
    assert "products" in schemas
    assert "orders" in schemas


def test_extract_table_schema_type(models_file):
    schemas = extract_orm_schemas(str(models_file))
    assert isinstance(schemas["products"], TableSchema)


def test_extract_column_names(models_file):
    schemas = extract_orm_schemas(str(models_file))
    col_names = [c.name for c in schemas["products"].columns]
    assert "id" in col_names
    assert "title" in col_names
    assert "active" in col_names


def test_extract_primary_key(models_file):
    schemas = extract_orm_schemas(str(models_file))
    assert "id" in schemas["products"].primary_keys


def test_extract_nullable(models_file):
    schemas = extract_orm_schemas(str(models_file))
    by_name = {c.name: c for c in schemas["products"].columns}
    assert by_name["active"].nullable is True
    assert by_name["title"].nullable is False


def test_invalid_path_raises(tmp_path):
    with pytest.raises(ImportError):
        extract_orm_schemas(str(tmp_path / "nonexistent.py"))
