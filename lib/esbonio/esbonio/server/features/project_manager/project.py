from __future__ import annotations

import json
import pathlib
import typing

import aiosqlite

from esbonio.server import Uri
from esbonio.sphinx_agent import types

if typing.TYPE_CHECKING:
    from typing import Any
    from typing import TypeVar

    import cattrs

    T = TypeVar("T")


class Project:
    """Represents a documentation project."""

    def __init__(self, dbpath: str | pathlib.Path, converter: cattrs.Converter):
        self.converter = converter
        self.dbpath = dbpath
        self._connection: aiosqlite.Connection | None = None

    async def close(self):
        if self._connection is not None:
            await self._connection.close()

    async def get_db(self) -> aiosqlite.Connection:
        if self._connection is None:
            self._connection = await aiosqlite.connect(self.dbpath)

        return self._connection

    def load_as(self, o: str, t: type[T]) -> T:
        return self.converter.structure(json.loads(o), t)

    async def uri_to_docname(self, uri: str | Uri) -> str | None:
        """Given a uri, look up the corresponding Sphinx docname."""
        db = await self.get_db()

        query = "SELECT docname FROM files WHERE uri = ?"
        cursor = await db.execute(query, (str(uri),))

        if (result := await cursor.fetchone()) is None:
            return None

        return result[0]

    async def docname_to_uri(self, docname: str) -> str | None:
        """Given a Sphinx docname, lookup the corresponding uri"""
        db = await self.get_db()

        query = "SELECT uri FROM files WHERE docname = ?"
        cursor = await db.execute(query, (docname,))

        if (result := await cursor.fetchone()) is None:
            return None

        return result[0]

    async def get_src_uris(self) -> list[Uri]:
        """Return all known source uris."""
        db = await self.get_db()

        query = "SELECT uri FROM files"
        async with db.execute(query) as cursor:
            results = await cursor.fetchall()
            return [Uri.parse(s[0]) for s in results]

    async def get_build_path(self, src_uri: Uri) -> str | None:
        """Get the build path associated with the given ``src_uri``."""
        db = await self.get_db()

        query = "SELECT urlpath FROM files WHERE uri = ?"
        async with db.execute(query, (str(src_uri.resolve()),)) as cursor:
            if (result := await cursor.fetchone()) is None:
                return None

            return result[0]

    async def get_config_value(self, name: str) -> Any | None:
        """Return the requested configuration value, if available."""

        db = await self.get_db()
        query = "SELECT value FROM config WHERE name = ?"
        cursor = await db.execute(query, (name,))

        if (row := await cursor.fetchone()) is None:
            return None

        (value,) = row
        return json.loads(value)

    async def get_directive(self, name: str) -> types.Directive | None:
        """Get the directive with the given name."""
        db = await self.get_db()

        query = "SELECT * FROM directives WHERE name = ?"
        cursor = await db.execute(query, (name,))
        result = await cursor.fetchone()

        return (
            types.Directive.from_db(self.load_as, *result)
            if result is not None
            else None
        )

    async def get_directives(self) -> list[tuple[str, str | None]]:
        """Get the directives known to Sphinx."""
        db = await self.get_db()

        query = "SELECT name, implementation FROM directives"
        cursor = await db.execute(query)
        return await cursor.fetchall()  # type: ignore[return-value]

    async def get_role(self, name: str) -> types.Role | None:
        """Get the role with the given name."""
        db = await self.get_db()

        query = "SELECT * FROM roles WHERE name = ?"
        cursor = await db.execute(query, (name,))
        result = await cursor.fetchone()

        return types.Role.from_db(self.load_as, *result) if result is not None else None

    async def get_roles(self) -> list[tuple[str, str | None]]:
        """Get the roles known to Sphinx."""
        db = await self.get_db()

        query = "SELECT name, implementation FROM roles"
        cursor = await db.execute(query)
        return await cursor.fetchall()  # type: ignore[return-value]

    async def get_document_symbols(self, src_uri: Uri) -> list[types.Symbol]:
        """Get the symbols for the given file."""
        db = await self.get_db()
        query = (
            "SELECT id, name, kind, detail, range, parent_id, order_id "
            "FROM symbols WHERE uri = ?"
        )
        cursor = await db.execute(query, (str(src_uri.resolve()),))
        return await cursor.fetchall()  # type: ignore[return-value]

    async def find_symbols(self, **kwargs) -> list[types.Symbol]:
        """Find symbols which match the given criteria."""
        db = await self.get_db()
        base_query = (
            "SELECT id, name, kind, detail, range, parent_id, order_id FROM symbols"
        )
        where: list[str] = []
        parameters: list[Any] = []

        for param, value in kwargs.items():
            where.append(f"{param} = ?")
            parameters.append(value)

        if where:
            conditions = " AND ".join(where)
            query = " ".join([base_query, "WHERE", conditions])
        else:
            query = base_query

        cursor = await db.execute(query, tuple(parameters))
        return await cursor.fetchall()  # type: ignore[return-value]

    async def get_workspace_symbols(
        self, query: str
    ) -> list[tuple[str, str, int, str, str, str]]:
        """Return all the workspace symbols matching the given query string"""

        db = await self.get_db()
        sql_query = """\
SELECT
    child.uri,
    child.name,
    child.kind,
    child.detail,
    child.range,
    COALESCE(parent.name, '') AS container_name
FROM
    symbols child
LEFT JOIN
    symbols parent ON (child.parent_id = parent.id AND child.uri = parent.uri)
WHERE
    child.name like ? or child.detail like ?;"""

        query_str = f"%{query}%"
        cursor = await db.execute(sql_query, (query_str, query_str))
        return await cursor.fetchall()  # type: ignore[return-value]

    async def get_diagnostics(self) -> dict[Uri, list[dict[str, Any]]]:
        """Get diagnostics for the project."""
        db = await self.get_db()
        cursor = await db.execute("SELECT * FROM diagnostics")
        results: dict[Uri, list[dict[str, Any]]] = {}

        for uri_str, item in await cursor.fetchall():
            uri = Uri.parse(uri_str)
            diagnostic = json.loads(item)
            results.setdefault(uri, []).append(diagnostic)

        return results
