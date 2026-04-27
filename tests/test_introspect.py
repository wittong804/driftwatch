"""Tests for driftwatch.introspect module."""

from __future__ import annotations

import pytest
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase

from driftwatch.introspect import ColumnInfo, TableSchema, introspect_database, introspect_table, get_inspector


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(200), nullable=True)


@pytest.fixture()
def sqlite_url(tmp_path):
    db_path = tmp_path / "test.db"
    url = f"sqlite:///{db_path}"
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    return url


def test_get_inspector_returns_inspector(sqlite_url):
    from sqlalchemy.engine import Inspector
    inspector = get_inspector(sqlite_url)
    assert isinstance(inspector, Inspector)


def test_introspect_table_columns(sqlite_url):
    inspector = get_inspector(sqlite_url)
    schema = introspect_table(inspector, "users")

    assert isinstance(schema, TableSchema)
    assert schema.name == "users"
    col_names = [c.name for c in schema.columns]
    assert "id" in col_names
    assert "name" in col_names
    assert "email" in col_names


def test_introspect_table_primary_key(sqlite_url):
    inspector = get_inspector(sqlite_url)
    schema = introspect_table(inspector, "users")
    assert "id" in schema.primary_keys


def test_introspect_table_nullable(sqlite_url):
    inspector = get_inspector(sqlite_url)
    schema = introspect_table(inspector, "users")
    by_name = {c.name: c for c in schema.columns}
    assert by_name["email"].nullable is True
    assert by_name["name"].nullable is False


def test_introspect_database_all_tables(sqlite_url):
    result = introspect_database(sqlite_url)
    assert "users" in result
    assert isinstance(result["users"], TableSchema)


def test_introspect_database_filter_tables(sqlite_url):
    result = introspect_database(sqlite_url, tables=["users"])
    assert "users" in result


def test_introspect_database_missing_table_excluded(sqlite_url):
    result = introspect_database(sqlite_url, tables=["nonexistent"])
    assert result == {}
