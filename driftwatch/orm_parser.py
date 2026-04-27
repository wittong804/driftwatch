"""Parse ORM model definitions to extract expected schema information."""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Dict, List, Optional

from driftwatch.introspect import ColumnInfo, TableSchema

try:
    from sqlalchemy import inspect as sa_inspect
    from sqlalchemy.orm import DeclarativeBase, DeclarativeMeta
except ImportError:  # pragma: no cover
    DeclarativeBase = None  # type: ignore
    DeclarativeMeta = None  # type: ignore


def _load_module_from_path(module_path: str):
    """Dynamically load a Python module from a file path."""
    path = Path(module_path).resolve()
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from path: {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def extract_orm_schemas(models_path: str) -> Dict[str, TableSchema]:
    """Load SQLAlchemy ORM models from *models_path* and extract table schemas.

    Supports both legacy ``DeclarativeMeta`` and modern ``DeclarativeBase``
    subclasses.

    Args:
        models_path: Path to a Python file containing ORM model definitions.

    Returns:
        Mapping of table name to TableSchema derived from ORM metadata.
    """
    module = _load_module_from_path(models_path)
    schemas: Dict[str, TableSchema] = {}

    for attr_name in dir(module):
        obj = getattr(module, attr_name)
        if not isinstance(obj, type):
            continue
        # Identify mapped ORM classes
        try:
            mapper = sa_inspect(obj)
        except Exception:
            continue

        table = getattr(mapper, "local_table", None)
        if table is None:
            continue

        pk_names = {col.name for col in table.primary_key.columns}
        columns: List[ColumnInfo] = [
            ColumnInfo(
                name=col.name,
                type=str(col.type),
                nullable=col.nullable if col.nullable is not None else True,
                default=str(col.default.arg) if col.default is not None else None,
                primary_key=col.name in pk_names,
            )
            for col in table.columns
        ]
        indexes = [idx.name for idx in table.indexes if idx.name]

        schemas[table.name] = TableSchema(
            name=table.name,
            columns=columns,
            primary_keys=list(pk_names),
            indexes=indexes,
        )

    return schemas
