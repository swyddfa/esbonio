from __future__ import annotations

import pathlib
import sqlite3
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import List
from typing import Literal
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Union


class Database:
    @dataclass
    class Column:
        name: str
        dtype: str
        notnull: bool = field(default=False)
        default: Optional[Any] = field(default=None)
        pk: int = field(default=0)

        @property
        def definition(self):
            # TODO: Is there a way to do this via a prepared statement?
            return f"{self.name} {self.dtype}"

    @dataclass
    class Table:
        name: str
        columns: List[Database.Column]

        @property
        def create_statement(self):
            """Return the SQL statement required to create this table."""
            # TODO: Is there a way to do this via a prepared statement?
            columns = ",".join([c.definition for c in self.columns])
            return "".join([f"CREATE TABLE {self.name} (", columns, ");"])

    def __init__(self, dbpath: Union[pathlib.Path, Literal[":memory:"]]):
        self.path = dbpath

        if isinstance(self.path, pathlib.Path) and not self.path.parent.exists():
            self.path.parent.mkdir(parents=True)

        self.db = sqlite3.connect(self.path)

        # Ensure that Write Ahead Logging is enabled.
        self.db.execute("PRAGMA journal_mode(WAL)")

        self._checked_tables: Set[str] = set()

    def _get_table(self, name: str) -> Optional[Table]:
        """Get the table with the given name, if it exists."""
        # TODO: SQLite does not seem to like '?' syntax in this statement...
        cursor = self.db.execute(f"PRAGMA table_info({name});")
        rows = cursor.fetchall()

        if len(rows) == 0:
            # Table does not exist
            return None

        columns = [
            self.Column(name=name, dtype=type_, notnull=notnull, default=default, pk=pk)
            for (_, name, type_, notnull, default, pk) in rows
        ]

        return self.Table(name=name, columns=columns)

    def _create_table(self, table: Table):
        """Create the given table."""
        cursor = self.db.cursor()

        # TODO: Is there a way to do this via a prepared statement?
        cursor.execute(f"DROP TABLE IF EXISTS {table.name}")
        cursor.execute(table.create_statement)
        self.db.commit()

    def clear_table(self, table: Table, **kwargs):
        """Clear the given table

        Parameters
        ----------
        kwargs
           Constraints to limit the rows that get cleared
        """

        # TODO: Is there a way to pass the table name as a '?' parameter?
        base_query = f"DELETE FROM {table.name}"  # noqa: S608
        where: List[str] = []
        parameters: List[Any] = []

        for param, value in kwargs.items():
            if value is None:
                where.append(f"{param} is null")
            else:
                where.append(f"{param} = ?")
                parameters.append(value)

        if where:
            conditions = " AND ".join(where)
            query = " ".join([base_query, "WHERE", conditions])
        else:
            query = base_query

        cursor = self.db.cursor()
        cursor.execute(query, tuple(parameters))
        self.db.commit()

    def ensure_table(self, table: Table):
        """Ensure that the given table exists in the database.

        If the table *does* exist, but has the wrong shape, it will be dropped and
        recreated.
        """
        # If we've already checked the table, then there's nothing to do
        if table.name in self._checked_tables:
            return

        if (existing := self._get_table(table.name)) is None:
            self._create_table(table)
            return

        # Are the tables compatible?
        if len(existing.columns) != len(table.columns):
            self._create_table(table)
        else:
            for existing_col, col in zip(existing.columns, table.columns):
                if existing_col.name != col.name or existing_col.dtype != col.dtype:
                    self._create_table(table)
                    break

        self._checked_tables.add(table.name)

    def insert_values(self, table: Table, values: List[Tuple]):
        """Insert the given values into the given table."""

        if len(values) == 0:
            return

        cursor = self.db.cursor()

        placeholder = "(" + ",".join(["?" for _ in range(len(values[0]))]) + ")"
        cursor.executemany(f"INSERT INTO {table.name} VALUES {placeholder}", values)  # noqa: S608
        self.db.commit()
