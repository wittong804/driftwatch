"""Compare introspected database schemas against ORM model definitions."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from driftwatch.introspect import TableSchema


@dataclass
class ColumnDiff:
    column_name: str
    issue: str
    db_value: Optional[str] = None
    orm_value: Optional[str] = None

    def __str__(self) -> str:
        parts = [f"  [{self.issue}] column '{self.column_name}'"]
        if self.db_value is not None:
            parts.append(f"    db : {self.db_value}")
        if self.orm_value is not None:
            parts.append(f"    orm: {self.orm_value}")
        return "\n".join(parts)


@dataclass
class TableDiff:
    table_name: str
    missing_in_db: List[str] = field(default_factory=list)
    missing_in_orm: List[str] = field(default_factory=list)
    column_diffs: List[ColumnDiff] = field(default_factory=list)

    @property
    def has_drift(self) -> bool:
        return bool(self.missing_in_db or self.missing_in_orm or self.column_diffs)

    def __str__(self) -> str:
        lines = [f"Table '{self.table_name}':"]
        for col in self.missing_in_db:
            lines.append(f"  [missing_in_db] column '{col}'")
        for col in self.missing_in_orm:
            lines.append(f"  [missing_in_orm] column '{col}'")
        for diff in self.column_diffs:
            lines.append(str(diff))
        return "\n".join(lines)


@dataclass
class DriftReport:
    missing_tables_in_db: List[str] = field(default_factory=list)
    missing_tables_in_orm: List[str] = field(default_factory=list)
    table_diffs: List[TableDiff] = field(default_factory=list)

    @property
    def has_drift(self) -> bool:
        return bool(
            self.missing_tables_in_db
            or self.missing_tables_in_orm
            or any(t.has_drift for t in self.table_diffs)
        )


def diff_schemas(
    db_schemas: Dict[str, TableSchema],
    orm_schemas: Dict[str, TableSchema],
) -> DriftReport:
    """Return a DriftReport describing differences between db and orm schemas."""
    report = DriftReport()

    db_tables = set(db_schemas.keys())
    orm_tables = set(orm_schemas.keys())

    report.missing_tables_in_db = sorted(orm_tables - db_tables)
    report.missing_tables_in_orm = sorted(db_tables - orm_tables)

    for table_name in sorted(db_tables & orm_tables):
        db_table = db_schemas[table_name]
        orm_table = orm_schemas[table_name]

        db_cols = {c.name: c for c in db_table.columns}
        orm_cols = {c.name: c for c in orm_table.columns}

        table_diff = TableDiff(table_name=table_name)
        table_diff.missing_in_db = sorted(set(orm_cols) - set(db_cols))
        table_diff.missing_in_orm = sorted(set(db_cols) - set(orm_cols))

        for col_name in sorted(set(db_cols) & set(orm_cols)):
            db_col = db_cols[col_name]
            orm_col = orm_cols[col_name]

            if db_col.nullable != orm_col.nullable:
                table_diff.column_diffs.append(
                    ColumnDiff(
                        column_name=col_name,
                        issue="nullable_mismatch",
                        db_value=str(db_col.nullable),
                        orm_value=str(orm_col.nullable),
                    )
                )

        if table_diff.has_drift:
            report.table_diffs.append(table_diff)

    return report
