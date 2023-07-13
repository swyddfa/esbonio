from __future__ import annotations

import inspect
import typing
from typing import Dict
from typing import Optional

import lsprotocol.types as lsp

from esbonio.server import LanguageFeature

from .client import make_sphinx_client
from .config import SphinxConfig

if typing.TYPE_CHECKING:
    from .client import SphinxClient


class SphinxManager(LanguageFeature):
    """Responsible for managing Sphinx application instances."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.clients: Dict[str, SphinxClient] = {}
        """Holds currently active Sphinx clients."""

        self.jobs = set()
        """Used to hold temporary references to background jobs."""

        self.handlers: Dict[str, set] = {}
        """Collection of handlers for various events."""

    def add_listener(self, event: str, handler):
        self.handlers.setdefault(event, set()).add(handler)

    def document_change(self, params: lsp.DidChangeTextDocumentParams):
        ...

    def document_close(self, params: lsp.DidCloseTextDocumentParams):
        ...

    async def document_open(self, params: lsp.DidOpenTextDocumentParams):
        await self.get_client(params.text_document.uri)

    async def document_save(self, params: lsp.DidSaveTextDocumentParams):
        await self.trigger_build(params.text_document.uri)

    async def trigger_build(self, uri: str):
        """Trigger a build for the relevant Sphinx application for the given uri."""
        client = await self.get_client(uri)
        if client is None:
            return

        result = await client.build()
        self.logger.debug("Build result: %s", result)

        # Notify listeners.
        for listener in self.handlers.get("build", set()):
            try:
                # TODO: Concurrent awaiting?
                res = listener(client.src_uri, result)
                if inspect.isawaitable(res):
                    await res
            except Exception:
                name = f"{listener}"
                self.logger.error("Error in build handler '%s'", name, exc_info=True)

    async def get_client(self, uri: str) -> Optional[SphinxClient]:
        """Given a uri, return the relevant sphinx client instance for it."""

        for srcdir, client in self.clients.items():
            if uri.startswith(srcdir):
                return client

        config = await self._get_user_config(uri)
        if config is None:
            return None

        resolved = config.resolve(uri, self.server.workspace, self.logger)
        if resolved is None:
            return None

        client = make_sphinx_client(self)
        await client.start(resolved)

        sphinx_info = await client.create_application(resolved)
        if sphinx_info is None:
            self.logger.error("No application object!")
            await client.stop()
            return None

        src_uri = client.src_uri
        if src_uri is None:
            self.logger.error("No src uri!")
            await client.stop()
            return None

        self.server.lsp.notify("sphinx/appCreated", sphinx_info)
        self.clients[src_uri] = client
        return client

    async def _get_user_config(self, uri: str) -> Optional[SphinxConfig]:
        """Return the user's Sphinx configuration for the given uri.

        Parameter
        ---------
        uri
           The uri to get the configuration for.

        Returns
        -------
        SphinxConfig | None
           The user's configuration.
           If ``None``, the config was not available.
        """
        params = lsp.ConfigurationParams(
            items=[lsp.ConfigurationItem(section="esbonio.sphinx", scope_uri=uri)]
        )
        result = await self.server.get_configuration_async(params)
        try:
            config = self.converter.structure(result[0], SphinxConfig)
            self.logger.debug("User config: %s", result[0])
            return config
        except Exception:
            self.logger.error(
                "Unable to parse sphinx configuration options", exc_info=True
            )
            return None
