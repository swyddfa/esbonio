from __future__ import annotations

import asyncio
import enum
import logging
import pathlib
import sys
import typing
from uuid import uuid4

import platformdirs
from pygls.client import JsonRPCClient
from pygls.protocol import JsonRPCProtocol

from esbonio.server import EventSource
from esbonio.server import Uri
from esbonio.sphinx_agent import types

from .config import SphinxConfig

if typing.TYPE_CHECKING:
    from typing import Any

    from .manager import SphinxManager


class ClientState(enum.Enum):
    """The set of possible states the client may be in."""

    Spawning = enum.auto()
    """The client process is being spwaned."""

    Starting = enum.auto()
    """The client is starting."""

    Restarting = enum.auto()
    """The client is restarting."""

    Running = enum.auto()
    """The client is running normally."""

    Building = enum.auto()
    """The client is currently building."""

    Errored = enum.auto()
    """The client has enountered some unrecoverable error and should not be used."""

    Exited = enum.auto()
    """The client is no longer running."""


sphinx_logger = logging.getLogger("sphinx")


class SphinxAgentProtocol(JsonRPCProtocol):
    """Describes the protocol spoken between the client below and the sphinx agent."""

    def get_message_type(self, method: str) -> Any | None:
        return types.METHOD_TO_MESSAGE_TYPE.get(method, None)

    def get_result_type(self, method: str) -> Any | None:
        return types.METHOD_TO_RESPONSE_TYPE.get(method, None)


class SphinxClient(JsonRPCClient):
    """JSON-RPC client used to drive a Sphinx application instance hosted in
    a separate subprocess.

    See :mod:`esbonio.sphinx_agent` for the implementation of the server component.
    """

    def __init__(
        self,
        config: SphinxConfig,
        logger: logging.Logger | None = None,
        protocol_cls=SphinxAgentProtocol,
        *args,
        **kwargs,
    ):
        super().__init__(*args, protocol_cls=protocol_cls, **kwargs)  # type: ignore[misc]

        self.id = str(uuid4())
        """The client's id."""

        self.config = config
        """Configuration values."""

        self.logger = logger or logging.getLogger(__name__)
        """The logger instance to use."""

        self.sphinx_pid: int = 0
        """The pid of the sphinx build process (or ``0`` if not known)"""

        self.sphinx_info: types.SphinxInfo | None = None
        """Information about the Sphinx application the client is connected to."""

        self.state: ClientState | None = None
        """The current state of the client."""

        self.exception: Exception | None = None
        """The most recently encountered exception (if any)"""

        self._events = EventSource(self.logger)
        """The sphinx client can emit events."""

        self._startup_task: asyncio.Task[Any] | None = None
        """The startup task."""

        self._stderr_forwarder: asyncio.Task[Any] | None = None
        """A task that forwards the server's stderr to the test process."""

    def __repr__(self):
        if self.state is None:
            return "SphinxClient<None>"

        if self.state == ClientState.Errored:
            return f"SphinxClient<{self.state.name}: {self.exception}>"

        state = self.state.name
        command = " ".join(self.config.build_command)
        return f"SphinxClient<{state}: {command}>"

    def __await__(self):
        """Makes the client await-able"""
        if self._startup_task is None:
            self._startup_task = asyncio.create_task(self.start())

        return self._startup_task.__await__()

    @property
    def converter(self):
        return self.protocol._converter

    @property
    def pid(self) -> int:
        """The pid of the process launched by the client

        .. important::

           When the user uses tools like ``uv`` this may be a different process to the
           actual Sphinx build process!. To get the pid of the sphinx build process use
           ``sphinx_pid``

        If no process is running this will return ``0``.
        """
        if self._server is None:
            return 0

        return self._server.pid

    @property
    def builder(self) -> str:
        """The sphinx application's builder name"""
        if self.sphinx_info is None:
            raise RuntimeError("sphinx_info is None, has the client been started?")

        return self.sphinx_info.builder_name

    @property
    def src_uri(self) -> Uri:
        """The src uri of the Sphinx application."""
        if self.sphinx_info is None:
            raise RuntimeError("sphinx_info is None, has the client been started?")

        return Uri.for_file(self.sphinx_info.src_dir)

    @property
    def conf_uri(self) -> Uri:
        """The conf uri of the Sphinx application."""
        if self.sphinx_info is None:
            raise RuntimeError("sphinx_info is None, has the client been started?")

        return Uri.for_file(self.sphinx_info.conf_dir)

    @property
    def db(self) -> pathlib.Path:
        """Connection to the associated database."""
        if self.sphinx_info is None:
            raise RuntimeError("sphinx_info is None, has the client been started?")

        return pathlib.Path(self.sphinx_info.dbpath)

    @property
    def build_uri(self) -> Uri:
        """The build uri of the Sphinx application."""
        if self.sphinx_info is None:
            raise RuntimeError("sphinx_info is None, has the client been started?")

        return Uri.for_file(self.sphinx_info.build_dir)

    def add_listener(self, event: str, handler):
        self._events.add_listener(event, handler)

    async def server_exit(self, server: asyncio.subprocess.Process):
        """Called when the sphinx agent process exits."""

        #   0: all good
        # -15: terminated
        if server.returncode not in {0, -15}:
            self.exception = RuntimeError(server.returncode)
            self._set_state(ClientState.Errored)
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

        if self.state != ClientState.Errored:
            self._set_state(ClientState.Exited)

    async def start_io(self, cmd: str, *args, **kwargs):
        await super().start_io(cmd, *args, **kwargs)

        # Forward the server's stderr to this process' stderr
        if self._server and self._server.stderr:
            self._stderr_forwarder = asyncio.create_task(forward_stderr(self._server))

    async def restart(self) -> SphinxClient:
        """Restart the client."""
        await self.stop()

        # We need to reset the client's stop event.
        self._stop_event.clear()

        self._set_state(ClientState.Restarting)
        return await self.start()

    async def start(self) -> SphinxClient:
        """Start the client."""

        # Only try starting once.
        if self.state not in {None, ClientState.Restarting}:
            return self

        try:
            self._set_state(ClientState.Spawning)

            sphinx = self.config.sphinx_command

            self.logger.debug("Python command: %r", sphinx.command)
            await self.start_io(*sphinx.command, env=sphinx.env, cwd=sphinx.cwd)

            result: types.InitializeResult = await self.protocol.send_request_async(
                "initialize", types.InitializeParams()
            )
            self.sphinx_pid = result.pid

            self._set_state(ClientState.Starting)

            params = types.CreateApplicationParams(
                command=self.config.build_command,
                config_overrides=self.config.config_overrides,
                context={
                    "cacheDir": platformdirs.user_cache_dir("esbonio", "swyddfa"),
                },
            )
            self.sphinx_info = await self.protocol.send_request_async(
                "sphinx/createApp", params
            )

            self._set_state(ClientState.Running)
            return self
        except Exception as exc:
            self.logger.debug("Unable to start SphinxClient: %s", exc, exc_info=True)

            self.exception = exc
            self._set_state(ClientState.Errored)

            return self

    def _set_state(self, new_state: ClientState):
        """Change the state of the client."""
        old_state, self.state = self.state, new_state

        self.logger.debug("SphinxClient[%s]: %s -> %s", self.id, old_state, new_state)
        self._events.trigger("state-change", self, old_state, new_state)

    async def stop(self):
        """Stop the client."""

        self.protocol.notify("exit", None)

        # Give the agent a little time to close.
        await asyncio.sleep(0.5)

        if self._stderr_forwarder:
            self._stderr_forwarder.cancel()

        self.logger.debug(self._async_tasks)
        await super().stop()

    async def build(
        self,
        *,
        filenames: list[str] | None = None,
        force_all: bool = False,
        content_overrides: dict[str, str] | None = None,
    ) -> types.BuildResult:
        """Trigger a Sphinx build."""

        params = types.BuildParams(
            filenames=filenames or [],
            force_all=force_all,
            content_overrides=content_overrides or {},
        )

        self._set_state(ClientState.Building)
        try:
            result = await self.protocol.send_request_async("sphinx/build", params)
            self._set_state(ClientState.Running)

            return result
        except Exception as exc:
            self.exception = exc
            self._set_state(ClientState.Errored)

            raise


async def forward_stderr(server: asyncio.subprocess.Process):
    if server.stderr is None:
        return

    # EOF is signalled with an empty bytestring
    while (line := await server.stderr.readline()) != b"":
        sphinx_logger.info(line.decode().rstrip())


def make_sphinx_client(manager: SphinxManager, config: SphinxConfig) -> SphinxClient:
    """Factory function for creating a ``SphinxClient`` instance.

    Parameters
    ----------
    manager
       The manager instance creating the client

    config
       The Sphinx configuration

    Returns
    -------
    SphinxClient
       The configured client
    """
    client = SphinxClient(config, logger=manager.logger)

    @client.feature("window/logMessage")
    def _on_msg(ls: SphinxClient, params):
        sphinx_logger.info(params.message)

    @client.feature("$/progress")
    def _on_progress(ls: SphinxClient, params):
        manager.report_progress(ls, params)

    return client


def make_test_sphinx_client(config: SphinxConfig) -> SphinxClient:
    """Factory function for creating a ``SphinxClient`` instance
    to use for testing."""
    logger = logging.getLogger("sphinx_client")
    logger.setLevel(logging.INFO)

    client = SphinxClient(config)

    @client.feature("window/logMessage")
    def _(params):
        print(params.message, file=sys.stderr)  # noqa: T201

    @client.feature("$/progress")
    def _on_progress(params):
        logger.info("%s", params)

    return client
