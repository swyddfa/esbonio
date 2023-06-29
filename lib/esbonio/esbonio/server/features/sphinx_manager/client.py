from __future__ import annotations

import asyncio
import json
import sys
import typing
from typing import Any
from typing import Optional
from typing import Type

import pygls.uris as Uri
from pygls.client import Client
from pygls.protocol import JsonRPCProtocol

import esbonio.sphinx_agent.types as types

from .config import SphinxConfig

if typing.TYPE_CHECKING:
    from .manager import SphinxManager


class SphinxAgentProtocol(JsonRPCProtocol):
    """Describes the protocol spoken between the client below and the sphinx agent."""

    def get_message_type(self, method: str) -> Any | None:
        return types.METHOD_TO_MESSAGE_TYPE.get(method, None)

    def get_result_type(self, method: str) -> Any | None:
        return types.METHOD_TO_RESPONSE_TYPE.get(method, None)


class SphinxClient(Client):
    """JSON-RPC client used to drive a Sphinx application instance hosted in
    a separate subprocess."""

    def __init__(self, manager: SphinxManager, *args, **kwargs):
        super().__init__(*args, protocol_cls=SphinxAgentProtocol, **kwargs)
        self.manager = manager
        self.logger = manager.logger

        self.sphinx_info: Optional[types.SphinxInfo] = None

    @property
    def builder(self) -> Optional[str]:
        """The sphinx application's builder name"""
        if self.sphinx_info is None:
            return None

        return self.sphinx_info.builder_name

    @property
    def src_dir(self) -> Optional[str]:
        """The src directory of the Sphinx application."""
        if self.sphinx_info is None:
            return None

        return self.sphinx_info.src_dir

    @property
    def src_uri(self) -> Optional[str]:
        """The src uri of the Sphinx application."""
        src_dir = self.src_dir
        if src_dir is None:
            return None

        return Uri.from_fs_path(src_dir)

    @property
    def conf_dir(self) -> Optional[str]:
        """The conf directory of the Sphinx application."""
        if self.sphinx_info is None:
            return None

        return self.sphinx_info.conf_dir

    @property
    def conf_uri(self) -> Optional[str]:
        """The conf uri of the Sphinx application."""
        conf_dir = self.conf_dir
        if conf_dir is None:
            return None

        return Uri.from_fs_path(conf_dir)

    @property
    def build_dir(self) -> Optional[str]:
        """The build directory of the Sphinx application."""
        if self.sphinx_info is None:
            return None

        return self.sphinx_info.build_dir

    @property
    def build_uri(self) -> Optional[str]:
        """The build uri of the Sphinx application."""
        build_dir = self.build_dir
        if build_dir is None:
            return None

        return Uri.from_fs_path(build_dir)

    async def start(self, config: SphinxConfig):
        """Start the sphinx agent."""
        command = []
        if config.enable_dev_tools:
            command.extend([sys.executable, "-m", "lsp_devtools", "agent", "--"])

        command.extend([*config.python_command, "-m", "sphinx_agent"])
        env = {"PYTHONPATH": ":".join([str(p) for p in config.python_path])}

        self.logger.debug("Sphinx agent env: %s", json.dumps(env, indent=2))
        self.logger.debug("Starting sphinx agent: %s", " ".join(command))

        await self.start_io(*command, env=env, cwd=config.cwd)

    async def server_exit(self, server: asyncio.subprocess.Process):
        """Called when the sphinx agent process exits."""
        self.logger.debug(f"Process exited with code: {server.returncode}")

        if server.returncode != 0:
            stderr = await server.stderr.read()
            self.logger.debug("Stderr:\n%s", stderr.decode("utf8"))

    async def create_application(self, config: SphinxConfig):
        """Create a sphinx application object."""

        if self.stopped:
            raise RuntimeError("Client is stopped.")

        params = types.CreateApplicationParams(
            command=config.build_command,
            enable_sync_scrolling=config.enable_sync_scrolling,
        )

        self.logger.debug("Starting sphinx: %s", " ".join(config.build_command))
        self.sphinx_info = await self.protocol.send_request_async(
            "sphinx/createApp", params
        )
        return self.sphinx_info

    async def build(self):
        """Trigger a Sphinx build."""
        return await self.protocol.send_request_async("sphinx/build", {})


def make_sphinx_client(manager: SphinxManager):
    client = SphinxClient(manager=manager)

    @client.feature("window/logMessage")
    def on_msg(ls: SphinxClient, params):
        ls.manager.server.show_message_log(params.message)

    return client
