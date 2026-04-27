"""Tests for driftwatch.diff — schema drift detection logic."""

import pytest

from driftwatch.introspect import ColumnInfo, TableSchema
from driftwatch.diff import diff_schemas, DriftReport, TableDiff, ColumnDiff


def make_table(name: str, columns: list) -> TableSchema:
    return TableSchema(table_name=name, columns=columns)


def col(name: str, type_: str = "VARCHAR", nullable: bool = True) -> ColumnInfo:
    return ColumnInfo(name=name, type=type_, nullable=nullable, default=None)


# --- DriftReport.has_drift ---

def test_empty_report_has_no_drift():
    report = DriftReport()
    assert not report.has_drift


def test_report_with_missing_table_has_drift():
    report = DriftReport(missing_tables_in_db=["users"])
    assert report.has_drift


# --- diff_schemas: table-level ---

def test_identical_schemas_no_drift():
    schema = {"users": make_table("users", [col("id"), col("email")])}
    report = diff_schemas(schema, schema)
    assert not report.has_drift
    assert report.missing_tables_in_db == []
    assert report.missing_tables_in_orm == []
    assert report.table_diffs == []


def test_table_in_orm_missing_from_db():
    db = {}
    orm = {"orders": make_table("orders", [col("id")])}
    report = diff_schemas(db, orm)
    assert report.has_drift
    assert "orders" in report.missing_tables_in_db
    assert report.missing_tables_in_orm == []


def test_table_in_db_missing_from_orm():
    db = {"legacy": make_table("legacy", [col("id")])}
    orm = {}
    report = diff_schemas(db, orm)
    assert report.has_drift
    assert "legacy" in report.missing_tables_in_orm
    assert report.missing_tables_in_db == []


# --- diff_schemas: column-level ---

def test_column_missing_in_db():
    db_schema = {"users": make_table("users", [col("id")])}
    orm_schema = {"users": make_table("users", [col("id"), col("email")])}
    report = diff_schemas(db_schema, orm_schema)
    assert report.has_drift
    assert len(report.table_diffs) == 1
    assert "email" in report.table_diffs[0].missing_in_db


def test_column_missing_in_orm():
    db_schema = {"users": make_table("users", [col("id"), col("created_at")])}
    orm_schema = {"users": make_table("users", [col("id")])}
    report = diff_schemas(db_schema, orm_schema)
    assert report.has_drift
    assert "created_at" in report.table_diffs[0].missing_in_orm


def test_nullable_mismatch_detected():
    db_schema = {"users": make_table("users", [col("email", nullable=True)])}
    orm_schema = {"users": make_table("users", [col("email", nullable=False)])}
    report = diff_schemas(db_schema, orm_schema)
    assert report.has_drift
    diffs = report.table_diffs[0].column_diffs
    assert len(diffs) == 1
    assert diffs[0].column_name == "email"
    assert diffs[0].issue == "nullable_mismatch"


def test_no_drift_when_nullable_matches():
    db_schema = {"users": make_table("users", [col("email", nullable=False)])}
    orm_schema = {"users": make_table("users", [col("email", nullable=False)])}
    report = diff_schemas(db_schema, orm_schema)
    assert not report.has_drift


# --- str representations ---

def test_column_diff_str():
    d = ColumnDiff("email", "nullable_mismatch", db_value="True", orm_value="False")
    text = str(d)
    assert "email" in text
    assert "nullable_mismatch" in text


def test_table_diff_str():
    td = TableDiff(table_name="users", missing_in_db=["bio"])
    text = str(td)
    assert "users" in text
    assert "bio" in text
