"""Database schema introspection utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Inspector


@dataclass
class ColumnInfo:
    name: str
    type: str
    nullable: bool
    default: Optional[str] = None
    primary_key: bool = False


@dataclass
class TableSchema:
    name: str
    columns: List[ColumnInfo] = field(default_factory=list)
    primary_keys: List[str] = field(default_factory=list)
    indexes: List[str] = field(default_factory=list)


def get_inspector(db_url: str) -> Inspector:
    """Create a SQLAlchemy inspector for the given database URL."""
    engine = create_engine(db_url)
    return inspect(engine)


def introspect_table(inspector: Inspector, table_name: str) -> TableSchema:
    """Introspect a single table and return its schema."""
    pk_columns = set(inspector.get_pk_constraint(table_name).get("constrained_columns", []))
    raw_columns = inspector.get_columns(table_name)
    raw_indexes = inspector.get_indexes(table_name)

    columns = [
        ColumnInfo(
            name=col["name"],
            type=str(col["type"]),
            nullable=col.get("nullable", True),
            default=str(col["default"]) if col.get("default") is not None else None,
            primary_key=col["name"] in pk_columns,
        )
        for col in raw_columns
    ]

    indexes = [idx["name"] for idx in raw_indexes if idx.get("name")]

    return TableSchema(
        name=table_name,
        columns=columns,
        primary_keys=list(pk_columns),
        indexes=indexes,
    )


def introspect_database(db_url: str, tables: Optional[List[str]] = None) -> Dict[str, TableSchema]:
    """Introspect all (or specified) tables in the database.

    Args:
        db_url: SQLAlchemy-compatible database URL.
        tables: Optional list of table names to restrict introspection to.

    Returns:
        Mapping of table name to TableSchema.
    """
    inspector = get_inspector(db_url)
    available = inspector.get_table_names()
    targets = [t for t in available if tables is None or t in tables]
    return {name: introspect_table(inspector, name) for name in targets}
