from __future__ import annotations

import typing
from typing import Dict
from typing import Optional

import lsprotocol.types as lsp
import pygls.uris as Uri

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
        self.jobs = set()

    def document_change(self, params: lsp.DidChangeTextDocumentParams):
        self.logger.debug("Changed document '%s'", params.text_document.uri)

    def document_close(self, params: lsp.DidCloseTextDocumentParams):
        self.logger.debug("Closed document '%s'", params.text_document.uri)

    async def document_open(self, params: lsp.DidOpenTextDocumentParams):
        self.logger.debug("Opened document '%s'", params.text_document.uri)
        await self.get_client(params.text_document.uri)

    async def document_save(self, params: lsp.DidSaveTextDocumentParams):
        self.logger.debug("Saved document '%s'", params.text_document.uri)

        client = await self.get_client(params.text_document.uri)
        if client is None:
            return

        result = await client.protocol.send_request_async("sphinx/build", {})
        self.logger.debug("Build result: %s", result)

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

        self.clients[src_uri] = client

        # Do an initial build in the background so that we're free to do other things.
        build_task = client.protocol.send_request_async("sphinx/build", {})
        self.jobs.add(build_task)
        build_task.add_done_callback(self.jobs.discard)

        return client
