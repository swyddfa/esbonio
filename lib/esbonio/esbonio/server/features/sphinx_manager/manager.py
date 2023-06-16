from __future__ import annotations

import hashlib
import importlib.util
import logging
import pathlib
import typing
from typing import Dict
from typing import List
from typing import Optional

import appdirs
import attrs
import lsprotocol.types as lsp
import pygls.uris as Uri
from pygls.workspace import Workspace

from esbonio.server import LanguageFeature

from .client import make_sphinx_client

if typing.TYPE_CHECKING:
    from .client import SphinxClient


def get_python_path() -> Optional[pathlib.Path]:
    spec = importlib.util.find_spec("esbonio.sphinx_agent")
    if spec is None:
        return None

    if spec.origin is None:
        return None

    # origin = .../esbonio/sphinx_agent/__init__.py
    agent = pathlib.Path(spec.origin)
    return agent.parent.parent


@attrs.define
class SphinxConfig:
    """Configuration for the sphinx application instance."""

    python_command: List[str] = attrs.field(factory=list)
    """The command to use when launching the python interpreter."""

    build_command: List[str] = attrs.field(factory=list)
    """The sphinx-build command to use."""

    cwd: str = attrs.field(default="")
    """The working directory to use."""

    python_path: Optional[pathlib.Path] = attrs.field(default=get_python_path())
    """The value of ``PYTHONPATH`` to use when injecting the sphinx agent into the
    target environment"""

    def resolve(
        self,
        uri: str,
        workspace: Workspace,
        logger: logging.Logger,
    ) -> "Optional[SphinxConfig]":
        """Resolve the configuration based on user provided values."""

        if self.python_path is None:
            logger.error("Unable to locate the sphinx agent")
            return None

        cwd = self._resolve_cwd(uri, workspace, logger)
        if cwd is None:
            return None

        build_command = self.build_command
        if len(build_command) == 0:
            build_command = self._guess_build_command(uri, logger)

        return SphinxConfig(
            cwd=cwd,
            python_command=self.python_command,
            build_command=build_command,
            python_path=self.python_path,
        )

    def _resolve_cwd(self, uri: str, workspace: Workspace, logger: logging.Logger):
        for folder_uri in workspace.folders.keys():
            if uri.startswith(folder_uri):
                break
        else:
            folder_uri = workspace.root_uri

        cwd = Uri.to_fs_path(folder_uri)
        if cwd is None:
            logger.error("Unable to determine working directory from '%s'", folder_uri)
            return None

        logger.debug("Cwd: %s", cwd)
        return cwd

    def _guess_build_command(self, uri: str, logger: logging.Logger) -> List[str]:
        """Try and guess something a sensible build command given the uri."""

        path = Uri.to_fs_path(uri)
        if path is None:
            return []

        # Search upwards from the given uri to see if we find something that looks like
        # a sphinx conf.py file.
        previous = None
        current = pathlib.Path(path)

        while previous != current:
            previous = current
            current = previous.parent

            conf_py = current / "conf.py"
            logger.debug("Trying path: %s", current)
            if conf_py.exists():
                cache = appdirs.user_cache_dir("esbonio", "swyddfa")
                project = hashlib.md5(str(current).encode()).hexdigest()
                build_dir = str(pathlib.Path(cache, project))
                return ["sphinx-build", "-M", "dirhtml", str(current), str(build_dir)]

        return []


class SphinxManager(LanguageFeature):
    """Responsible for managing Sphinx application instances."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.clients: Dict[str, SphinxClient] = {}

    def document_change(self, params: lsp.DidChangeTextDocumentParams):
        self.logger.debug("Changed document '%s'", params.text_document.uri)

    def document_close(self, params: lsp.DidCloseTextDocumentParams):
        self.logger.debug("Closed document '%s'", params.text_document.uri)

    async def document_open(self, params: lsp.DidOpenTextDocumentParams):
        self.logger.debug("Opened document '%s'", params.text_document.uri)
        await self.get_client(params.text_document.uri)

    def document_save(self, params: lsp.DidSaveTextDocumentParams):
        self.logger.debug("Saved document '%s'", params.text_document.uri)

    async def get_client(self, uri: str) -> Optional[SphinxClient]:
        """Given a uri, return the relevant sphinx client instance for it."""

        for srcdir, client in self.clients.items():
            if uri.startswith(srcdir):
                return client

        params = lsp.ConfigurationParams(
            items=[lsp.ConfigurationItem(section="esbonio.sphinx", scope_uri=uri)]
        )
        result = await self.server.get_configuration_async(params)
        try:
            config = self.converter.structure(result[0], SphinxConfig)
            self.logger.debug("User config: %s", config)
        except Exception:
            self.logger.error(
                "Unable to parse sphinx configuration options", exc_info=True
            )
            return None

        resolved = config.resolve(uri, self.server.workspace, self.logger)
        if resolved is None:
            return None

        if len(resolved.build_command) == 0:
            self.logger.error("Unable to start Sphinx: missing build command")
            return None

        command = [*resolved.python_command, "-m", "sphinx_agent"]
        self.logger.debug("Starting sphinx agent: %s", " ".join(command))

        client = make_sphinx_client(self)
        await client.start_io(
            *command, env={"PYTHONPATH": resolved.python_path}, cwd=resolved.cwd
        )

        if client.stopped:
            return None

        self.logger.debug("Starting sphinx: %s", " ".join(resolved.build_command))
        response = await client.protocol.send_request_async(
            "sphinx/createApp", {"command": resolved.build_command}
        )
        self.logger.debug("Sphinx started: %s", response)

        src_uri = Uri.from_fs_path(response.src_dir)
        if src_uri is None:
            self.logger.error("Invalid srcdir '%s'", response.src_dir)
            await client.stop()
            return None

        self.clients[src_uri] = client
        return client
