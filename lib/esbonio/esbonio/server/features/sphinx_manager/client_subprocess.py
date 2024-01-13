"""Subprocess implementation of the ``SphinxClient`` protocol."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
import typing

import aiosqlite
from pygls import IS_WIN
from pygls.client import JsonRPCClient
from pygls.protocol import JsonRPCProtocol

import esbonio.sphinx_agent.types as types
from esbonio.server import Uri

from .config import SphinxConfig

if typing.TYPE_CHECKING:
    from typing import Any
    from typing import Dict
    from typing import List
    from typing import Optional
    from typing import Tuple

    from .client import SphinxClient
    from .manager import SphinxManager


class SphinxAgentProtocol(JsonRPCProtocol):
    """Describes the protocol spoken between the client below and the sphinx agent."""

    def get_message_type(self, method: str) -> Any | None:
        return types.METHOD_TO_MESSAGE_TYPE.get(method, None)

    def get_result_type(self, method: str) -> Any | None:
        return types.METHOD_TO_RESPONSE_TYPE.get(method, None)


class SubprocessSphinxClient(JsonRPCClient):
    """JSON-RPC client used to drive a Sphinx application instance hosted in
    a separate subprocess.

    See :mod:`esbonio.sphinx_agent` for the implementation of the server component.
    """

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        protocol_cls=SphinxAgentProtocol,
        *args,
        **kwargs,
    ):
        super().__init__(protocol_cls=protocol_cls, *args, **kwargs)  # type: ignore[misc]
        self.logger = logger or logging.getLogger(__name__)

        self.sphinx_info: Optional[types.SphinxInfo] = None

        self._connection: Optional[aiosqlite.Connection] = None
        self._building = False

    @property
    def converter(self):
        return self.protocol._converter

    @property
    def id(self) -> Optional[str]:
        """The id of the Sphinx instance."""
        if self.sphinx_info is None:
            return None

        return self.sphinx_info.id

    @property
    def building(self) -> bool:
        return self._building

    @property
    def builder(self) -> Optional[str]:
        """The sphinx application's builder name"""
        if self.sphinx_info is None:
            return None

        return self.sphinx_info.builder_name

    @property
    def src_uri(self) -> Optional[Uri]:
        """The src uri of the Sphinx application."""
        if self.sphinx_info is None:
            return None

        return Uri.for_file(self.sphinx_info.src_dir)

    @property
    def conf_uri(self) -> Optional[Uri]:
        """The conf uri of the Sphinx application."""
        if self.sphinx_info is None:
            return None

        return Uri.for_file(self.sphinx_info.conf_dir)

    @property
    def db(self) -> Optional[aiosqlite.Connection]:
        """Connection to the associated database."""
        return self._connection

    @property
    def build_uri(self) -> Optional[Uri]:
        """The build uri of the Sphinx application."""
        if self.sphinx_info is None:
            return None

        return Uri.for_file(self.sphinx_info.build_dir)

    async def server_exit(self, server: asyncio.subprocess.Process):
        """Called when the sphinx agent process exits."""

        #   0: all good
        # -15: terminated
        if server.returncode not in {0, -15}:
            self.logger.error(
                f"sphinx-agent process exited with code: {server.returncode}"
            )

            if server.stderr is not None:
                stderr = await server.stderr.read()
                self.logger.error("Stderr:\n%s", stderr.decode("utf8"))

        # TODO: Should the upstream base client be doing this?
        # Cancel any pending futures.
        for id_, fut in self.protocol._request_futures.items():
            message = "Cancelled" if fut.cancel() else "Unable to cancel"
            self.logger.debug(
                "%s future '%s' for pending request '%s'", message, fut, id_
            )

    async def start(self, config: SphinxConfig):
        """Start the client."""

        if len(config.python_command) == 0:
            raise ValueError("No python environment configured")

        command = []

        if config.enable_dev_tools and (
            lsp_devtools := self._get_lsp_devtools_command()
        ):
            command.extend([lsp_devtools, "agent", "--"])

        command.extend([*config.python_command, "-m", "sphinx_agent"])
        env = get_sphinx_env(config)

        self.logger.debug("Sphinx agent env: %s", json.dumps(env, indent=2))
        self.logger.debug("Starting sphinx agent: %s", " ".join(command))

        await self.start_io(*command, env=env, cwd=config.cwd)

    def _get_lsp_devtools_command(self) -> Optional[str]:
        # Assumes that the user has `lsp-devtools` available on their PATH
        # TODO: Windows support
        result = subprocess.run(["command", "-v", "lsp-devtools"], capture_output=True)
        if result.returncode == 0:
            lsp_devtools = result.stdout.decode("utf8").strip()
            return lsp_devtools

        stderr = result.stderr.decode("utf8").strip()
        self.logger.debug("Unable to locate lsp-devtools command", stderr)
        return None

    async def stop(self):
        """Stop the client."""

        self.protocol.notify("exit", None)
        if self._connection:
            await self._connection.close()

        # Give the agent a little time to close.
        # await asyncio.sleep(0.5)
        await super().stop()

    async def create_application(self, config: SphinxConfig) -> types.SphinxInfo:
        """Create a sphinx application object."""

        params = types.CreateApplicationParams(
            command=config.build_command,
            enable_sync_scrolling=config.enable_sync_scrolling,
        )

        sphinx_info = await self.protocol.send_request_async("sphinx/createApp", params)
        self.sphinx_info = sphinx_info

        try:
            self._connection = await aiosqlite.connect(sphinx_info.dbpath)
        except Exception:
            self.logger.error("Unable to connect to database", exc_info=True)

        return sphinx_info

    async def build(
        self,
        *,
        filenames: Optional[List[str]] = None,
        force_all: bool = False,
        content_overrides: Optional[Dict[str, str]] = None,
    ) -> types.BuildResult:
        """Trigger a Sphinx build."""

        params = types.BuildParams(
            filenames=filenames or [],
            force_all=force_all,
            content_overrides=content_overrides or {},
        )

        self._building = True
        try:
            result = await self.protocol.send_request_async("sphinx/build", params)
        finally:
            self._building = False

        return result

    async def get_src_uris(self) -> List[Uri]:
        """Return all known source uris."""

        if self.db is None:
            return []

        query = "SELECT uri FROM files"
        async with self.db.execute(query) as cursor:
            results = await cursor.fetchall()
            return [Uri.parse(s[0]) for s in results]

    async def get_build_path(self, src_uri: Uri) -> Optional[str]:
        """Get the build path associated with the given ``src_uri``."""

        if self.db is None:
            return None

        query = "SELECT urlpath FROM files WHERE uri = ?"
        async with self.db.execute(query, (str(src_uri.resolve()),)) as cursor:
            if (result := await cursor.fetchone()) is None:
                return None

            return result[0]

    async def get_config_value(self, name: str) -> Optional[Any]:
        """Return the requested configuration value, if available."""
        if self.db is None:
            return None

        query = "SELECT value FROM config WHERE name = ?"
        cursor = await self.db.execute(query, (name,))

        if (row := await cursor.fetchone()) is None:
            return None

        (value,) = row
        return json.loads(value)

    async def get_directives(self) -> List[Tuple[str, Optional[str]]]:
        """Get the directives known to Sphinx."""
        if self.db is None:
            return []

        query = "SELECT name, implementation FROM directives"
        cursor = await self.db.execute(query)
        return await cursor.fetchall()  # type: ignore[return-value]

    async def get_document_symbols(self, src_uri: Uri) -> List[types.Symbol]:
        """Get the symbols for the given file."""
        if self.db is None:
            return []

        query = (
            "SELECT id, name, kind, detail, range, parent_id, order_id "
            "FROM symbols WHERE uri = ?"
        )
        cursor = await self.db.execute(query, (str(src_uri.resolve()),))
        return await cursor.fetchall()  # type: ignore[return-value]

    async def find_symbols(self, **kwargs) -> List[types.Symbol]:
        """Find symbols which match the given criteria."""
        if self.db is None:
            return []

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

        cursor = await self.db.execute(query, tuple(parameters))
        return await cursor.fetchall()  # type: ignore[return-value]

    async def get_workspace_symbols(
        self, query: str
    ) -> List[Tuple[str, str, int, str, str, str]]:
        """Return all the workspace symbols matching the given query string"""

        if self.db is None:
            return []

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
        cursor = await self.db.execute(sql_query, (query_str, query_str))
        return await cursor.fetchall()  # type: ignore[return-value]

    async def get_diagnostics(self) -> Dict[Uri, List[Dict[str, Any]]]:
        """Get diagnostics for the project."""
        if self.db is None:
            return {}

        cursor = await self.db.execute("SELECT * FROM diagnostics")
        results: Dict[Uri, List[Dict[str, Any]]] = {}

        for uri_str, item in await cursor.fetchall():
            uri = Uri.parse(uri_str)
            diagnostic = json.loads(item)
            results.setdefault(uri, []).append(diagnostic)

        return results


def make_subprocess_sphinx_client(manager: SphinxManager) -> SphinxClient:
    """Factory function for creating a ``SubprocessSphinxClient`` instance.

    Parameters
    ----------
    manager
       The manager instance creating the client

    Returns
    -------
    SphinxClient
       The configured client
    """
    client = SubprocessSphinxClient(logger=manager.logger)

    @client.feature("window/logMessage")
    def _on_msg(ls: SubprocessSphinxClient, params):
        manager.server.show_message_log(params.message)

    @client.feature("$/progress")
    def _on_progress(ls: SubprocessSphinxClient, params):
        manager.report_progress(ls, params)

    return client


def make_test_sphinx_client() -> SubprocessSphinxClient:
    """Factory function for creating a ``SubprocessSphinxClient`` instance
    to use for testing."""
    logger = logging.getLogger("sphinx_client")
    logger.setLevel(logging.INFO)

    client = SubprocessSphinxClient()

    @client.feature("window/logMessage")
    def _(params):
        logger.info("%s", params.message)

    @client.feature("$/progress")
    def _on_progress(params):
        logger.info("%s", params)

    return client


def get_sphinx_env(config: SphinxConfig) -> Dict[str, str]:
    """Return the set of environment variables to use with the Sphinx process."""
    env = {"PYTHONPATH": os.pathsep.join([str(p) for p in config.python_path])}

    passthrough = set(config.env_passthrough)
    if IS_WIN and "SYSTEMROOT" not in passthrough:
        passthrough.add("SYSTEMROOT")

    for envname in passthrough:
        value = os.environ.get(envname, None)
        if value is not None:
            if envname == "PYTHONPATH":
                env["PYTHONPATH"] = f"{env['PYTHONPATH']}{os.pathsep}{value}"
            else:
                env[envname] = value

    return env
