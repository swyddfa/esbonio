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
from typing import List
from typing import Optional

from pygls import IS_WIN
from pygls.client import JsonRPCClient
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
        self._building = False
        self._build_file_map: Dict[Uri, str] = {}
        self._diagnostics: Dict[Uri, List[types.Diagnostic]] = {}

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
    def diagnostics(self) -> Dict[Uri, List[types.Diagnostic]]:
        """Any diagnostics associated with the project.

        These are automatically updated with each build.
        """
        return self._diagnostics

    @property
    def build_file_map(self) -> Dict[Uri, str]:
        """Mapping of source files to their corresponing output path."""
        return self._build_file_map

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
        command = []
        if config.enable_dev_tools:
            command.extend([sys.executable, "-m", "lsp_devtools", "agent", "--"])

        command.extend([*config.python_command, "-m", "sphinx_agent"])
        env = get_sphinx_env(config)

        self.logger.debug("Sphinx agent env: %s", json.dumps(env, indent=2))
        self.logger.debug("Starting sphinx agent: %s", " ".join(command))

        await self.start_io(*command, env=env, cwd=config.cwd)

    async def stop(self):
        """Stop the client."""
        self.protocol.notify("exit", None)

        # Give the agent a little time to close.
        await asyncio.sleep(0.5)
        await super().stop()

    async def create_application(self, config: SphinxConfig) -> types.SphinxInfo:
        """Create a sphinx application object."""

        params = types.CreateApplicationParams(
            command=config.build_command,
            enable_sync_scrolling=config.enable_sync_scrolling,
        )

        sphinx_info = await self.protocol.send_request_async("sphinx/createApp", params)
        self.sphinx_info = sphinx_info
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

        result = await self.protocol.send_request_async("sphinx/build", params)
        self._building = False

        self._diagnostics = {
            Uri.for_file(fpath): items for fpath, items in result.diagnostics.items()
        }

        self._build_file_map = {
            Uri.for_file(src): out for src, out in result.build_file_map.items()
        }

        return result


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


def make_test_sphinx_client() -> SubprocessSphinxClient:
    """Factory function for creating a ``SubprocessSphinxClient`` instance
    to use for testing."""
    logger = logging.getLogger("sphinx_client")
    logger.setLevel(logging.INFO)

    client = SubprocessSphinxClient()

    @client.feature("window/logMessage")
    def _(params):
        logger.info("%s", params.message)

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
            if envname == "PYTHONPATH":
                env["PYTHONPATH"] = f"{env['PYTHONPATH']}:{value}"
            else:
                env[envname] = value

    return env
