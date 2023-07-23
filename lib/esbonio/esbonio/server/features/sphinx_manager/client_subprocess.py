"""Subprocess implementation of the ``SphinxClient`` protocol."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import typing
from typing import Any
from typing import Dict
from typing import Optional

from pygls import IS_WIN
from pygls.client import Client
from pygls.protocol import JsonRPCProtocol

import esbonio.sphinx_agent.types as types
from esbonio.server import Uri

from .config import SphinxConfig

if typing.TYPE_CHECKING:
    from .client import SphinxClient
    from .manager import SphinxManager


class SphinxAgentProtocol(JsonRPCProtocol):
    """Describes the protocol spoken between the client below and the sphinx agent."""

    def get_message_type(self, method: str) -> Any | None:
        return types.METHOD_TO_MESSAGE_TYPE.get(method, None)

    def get_result_type(self, method: str) -> Any | None:
        return types.METHOD_TO_RESPONSE_TYPE.get(method, None)


class SubprocessSphinxClient(Client):
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
    def build_uri(self) -> Optional[Uri]:
        """The build uri of the Sphinx application."""
        if self.sphinx_info is None:
            return None

        return Uri.for_file(self.sphinx_info.build_dir)

    async def server_exit(self, server: asyncio.subprocess.Process):
        """Called when the sphinx agent process exits."""
        self.logger.debug(f"Process exited with code: {server.returncode}")

        if server.returncode != 0 and server.stderr is not None:
            stderr = await server.stderr.read()
            self.logger.debug("Stderr:\n%s", stderr.decode("utf8"))

        # TODO: Should the upstream base client be doing this?
        # Cancel any pending futures.
        for id_, fut in self.protocol._request_futures.items():
            message = "Cancelled" if fut.cancel() else "Unable to cancel"
            self.logger.debug(
                "%s future '%s' for pending request '%s'", message, fut, id_
            )

    async def create_application(self, config: SphinxConfig) -> types.SphinxInfo:
        """Start the sphinx agent and create a sphinx application object."""

        command = []
        if config.enable_dev_tools:
            command.extend([sys.executable, "-m", "lsp_devtools", "agent", "--"])

        command.extend([*config.python_command, "-m", "sphinx_agent"])
        env = get_sphinx_env(config)

        self.logger.debug("Sphinx agent env: %s", json.dumps(env, indent=2))
        self.logger.debug("Starting sphinx agent: %s", " ".join(command))

        await self.start_io(*command, env=env, cwd=config.cwd)

        params = types.CreateApplicationParams(
            command=config.build_command,
            enable_sync_scrolling=config.enable_sync_scrolling,
        )

        sphinx_info = await self.protocol.send_request_async("sphinx/createApp", params)
        self.sphinx_info = sphinx_info
        return sphinx_info

    async def build(self):
        """Trigger a Sphinx build."""
        return await self.protocol.send_request_async("sphinx/build", {})


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

    return client


def get_sphinx_env(config: SphinxConfig) -> Dict[str, str]:
    """Return the set of environment variables to use with the Sphinx process."""
    env = {"PYTHONPATH": ":".join([str(p) for p in config.python_path])}

    passthrough = set(config.env_passthrough)
    if IS_WIN and "SYSTEMROOT" not in passthrough:
        passthrough.add("SYSTEMROOT")

    for envname in passthrough:
        value = os.environ.get(envname, None)
        if value is not None:
            env[envname] = value

    return env
