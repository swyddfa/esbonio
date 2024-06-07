from __future__ import annotations

import json
import pathlib
import typing

import aiosqlite

from esbonio.server import Uri
from esbonio.sphinx_agent import types

if typing.TYPE_CHECKING:
    from typing import Any
    from typing import Dict
    from typing import List
    from typing import Optional
    from typing import Tuple
    from typing import Type
    from typing import TypeVar
    from typing import Union

    import cattrs

    T = TypeVar("T")


class Project:
    """Represents a documentation project."""

    def __init__(self, dbpath: Union[str, pathlib.Path], converter: cattrs.Converter):
        self.converter = converter
        self.dbpath = dbpath
        self._connection: Optional[aiosqlite.Connection] = None

    async def close(self):
        if self._connection is not None:
            await self._connection.close()

    async def get_db(self) -> aiosqlite.Connection:
        if self._connection is None:
            self._connection = await aiosqlite.connect(self.dbpath)

        return self._connection

    def load_as(self, o: str, t: Type[T]) -> T:
        return self.converter.structure(json.loads(o), t)

    async def get_src_uris(self) -> List[Uri]:
        """Return all known source uris."""
        db = await self.get_db()

        query = "SELECT uri FROM files"
        async with db.execute(query) as cursor:
            results = await cursor.fetchall()
            return [Uri.parse(s[0]) for s in results]

    async def get_build_path(self, src_uri: Uri) -> Optional[str]:
        """Get the build path associated with the given ``src_uri``."""
        db = await self.get_db()

        query = "SELECT urlpath FROM files WHERE uri = ?"
        async with db.execute(query, (str(src_uri.resolve()),)) as cursor:
            if (result := await cursor.fetchone()) is None:
                return None

            return result[0]

    async def get_config_value(self, name: str) -> Optional[Any]:
        """Return the requested configuration value, if available."""

        db = await self.get_db()
        query = "SELECT value FROM config WHERE name = ?"
        cursor = await db.execute(query, (name,))

        if (row := await cursor.fetchone()) is None:
            return None

        (value,) = row
        return json.loads(value)

    async def get_directives(self) -> List[Tuple[str, Optional[str]]]:
        """Get the directives known to Sphinx."""
        db = await self.get_db()

        query = "SELECT name, implementation FROM directives"
        cursor = await db.execute(query)
        return await cursor.fetchall()  # type: ignore[return-value]

    async def get_role(self, name: str) -> Optional[types.Role]:
        """Get the roles known to Sphinx."""
        db = await self.get_db()

        query = "SELECT * FROM roles WHERE name = ?"
        cursor = await db.execute(query, (name,))
        result = await cursor.fetchone()

        return types.Role.from_db(self.load_as, *result) if result is not None else None

    async def get_roles(self) -> List[Tuple[str, Optional[str]]]:
        """Get the roles known to Sphinx."""
        db = await self.get_db()

        query = "SELECT name, implementation FROM roles"
        cursor = await db.execute(query)
        return await cursor.fetchall()  # type: ignore[return-value]

    async def get_document_symbols(self, src_uri: Uri) -> List[types.Symbol]:
        """Get the symbols for the given file."""
        db = await self.get_db()
        query = (
            "SELECT id, name, kind, detail, range, parent_id, order_id "
            "FROM symbols WHERE uri = ?"
        )
        cursor = await db.execute(query, (str(src_uri.resolve()),))
        return await cursor.fetchall()  # type: ignore[return-value]

    async def find_symbols(self, **kwargs) -> List[types.Symbol]:
        """Find symbols which match the given criteria."""
        db = await self.get_db()
        base_query = (
            "SELECT id, name, kind, detail, range, parent_id, order_id FROM symbols"
        )
        where: List[str] = []
        parameters: List[Any] = []

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
    ) -> List[Tuple[str, str, int, str, str, str]]:
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

    async def get_diagnostics(self) -> Dict[Uri, List[Dict[str, Any]]]:
        """Get diagnostics for the project."""
        db = await self.get_db()
        cursor = await db.execute("SELECT * FROM diagnostics")
        results: Dict[Uri, List[Dict[str, Any]]] = {}

        for uri_str, item in await cursor.fetchall():
            uri = Uri.parse(uri_str)
            diagnostic = json.loads(item)
            results.setdefault(uri, []).append(diagnostic)

        return results
