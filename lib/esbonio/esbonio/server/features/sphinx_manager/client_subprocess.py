"""Subprocess implementation of the ``SphinxClient`` protocol."""

from __future__ import annotations

import asyncio
import logging
import os
import pathlib
import subprocess
import sys
import typing
from uuid import uuid4

from pygls.client import JsonRPCClient
from pygls.protocol import JsonRPCProtocol

from esbonio.server import EventSource
from esbonio.server import Uri
from esbonio.sphinx_agent import types

from .client import ClientState
from .config import SphinxConfig

if typing.TYPE_CHECKING:
    from typing import Any
    from typing import Dict
    from typing import List
    from typing import Optional

    from .client import SphinxClient
    from .manager import SphinxManager


sphinx_logger = logging.getLogger("sphinx")


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
        config: SphinxConfig,
        logger: Optional[logging.Logger] = None,
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

        self.sphinx_info: Optional[types.SphinxInfo] = None
        """Information about the Sphinx application the client is connected to."""

        self.state: Optional[ClientState] = None
        """The current state of the client."""

        self.exception: Optional[Exception] = None
        """The most recently encountered exception (if any)"""

        self._events = EventSource(self.logger)
        """The sphinx client can emit events."""

        self._startup_task: Optional[asyncio.Task] = None
        """The startup task."""

        self._stderr_forwarder: Optional[asyncio.Task] = None
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
            self._set_state(ClientState.Starting)
            command = get_start_command(self.config, self.logger)
            env = get_sphinx_env(self.config)

            self.logger.debug("Starting sphinx agent: %s", " ".join(command))
            await self.start_io(*command, env=env, cwd=self.config.cwd)

            params = types.CreateApplicationParams(
                command=self.config.build_command,
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

        if self.state in {ClientState.Running, ClientState.Building}:
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


async def forward_stderr(server: asyncio.subprocess.Process):
    if server.stderr is None:
        return

    # EOF is signalled with an empty bytestring
    while (line := await server.stderr.readline()) != b"":
        sphinx_logger.info(line.decode().rstrip())


def make_subprocess_sphinx_client(
    manager: SphinxManager, config: SphinxConfig
) -> SphinxClient:
    """Factory function for creating a ``SubprocessSphinxClient`` instance.

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
    client = SubprocessSphinxClient(config, logger=manager.logger)

    @client.feature("window/logMessage")
    def _on_msg(ls: SubprocessSphinxClient, params):
        sphinx_logger.info(params.message)

    @client.feature("$/progress")
    def _on_progress(ls: SubprocessSphinxClient, params):
        manager.report_progress(ls, params)

    return client


def make_test_sphinx_client(config: SphinxConfig) -> SubprocessSphinxClient:
    """Factory function for creating a ``SubprocessSphinxClient`` instance
    to use for testing."""
    logger = logging.getLogger("sphinx_client")
    logger.setLevel(logging.INFO)

    client = SubprocessSphinxClient(config)

    @client.feature("window/logMessage")
    def _(params):
        print(params.message, file=sys.stderr)  # noqa: T201

    @client.feature("$/progress")
    def _on_progress(params):
        logger.info("%s", params)

    return client


def get_sphinx_env(config: SphinxConfig) -> Dict[str, str]:
    """Return the set of environment variables to use with the Sphinx process."""

    env = {
        "PYTHONUNBUFFERED": "1",
        "PYTHONPATH": os.pathsep.join([str(p) for p in config.python_path]),
    }
    for envname, value in os.environ.items():
        # Don't pass any vars we've explictly set.
        if envname in env:
            continue

        env[envname] = value

    return env


def get_start_command(config: SphinxConfig, logger: logging.Logger):
    """Return the command to use to start the sphinx agent."""

    command = []

    if len(config.python_command) == 0:
        raise ValueError("No python environment configured")

    if config.enable_dev_tools:
        # Assumes that the user has `lsp-devtools` available on their PATH
        # TODO: Windows support
        result = subprocess.run(
            ["command", "-v", "lsp-devtools"],  # noqa: S607
            capture_output=True,
            check=False,
        )

        if result.returncode == 0:
            lsp_devtools = result.stdout.decode("utf8").strip()
            command.extend([lsp_devtools, "agent", "--"])

        else:
            stderr = result.stderr.decode("utf8").strip()
            logger.debug("Unable to locate lsp-devtools command\n%s", stderr)

    command.extend([*config.python_command, "-m", "sphinx_agent"])
    return command
