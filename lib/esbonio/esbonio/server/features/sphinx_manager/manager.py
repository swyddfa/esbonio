from __future__ import annotations

import asyncio
import inspect
import typing
from typing import Callable
from typing import Dict
from typing import Optional

import lsprotocol.types as lsp

from esbonio.server import LanguageFeature
from esbonio.server import Uri

from .config import SphinxConfig

if typing.TYPE_CHECKING:
    from .client import SphinxClient


SphinxClientFactory = Callable[["SphinxManager"], "SphinxClient"]


class SphinxManager(LanguageFeature):
    """Responsible for managing Sphinx application instances."""

    def __init__(self, client_factory: SphinxClientFactory, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.client_factory = client_factory
        """Used to create new Sphinx client instances."""

        self.clients: Dict[Uri, SphinxClient] = {}
        """Holds currently active Sphinx clients."""

        self.handlers: Dict[str, set] = {}
        """Collection of handlers for various events."""

        self._pending_builds: Dict[str, asyncio.Task] = {}
        """Holds tasks that will trigger a build after a given delay if not cancelled."""

        self._client_creating: Optional[asyncio.Task] = None
        """If set, indicates we're in the process of setting up a new client."""

    def add_listener(self, event: str, handler):
        self.handlers.setdefault(event, set()).add(handler)

    async def document_change(self, params: lsp.DidChangeTextDocumentParams):
        if (uri := Uri.parse(params.text_document.uri)) is None:
            return

        client = await self.get_client(uri)
        if client is None or client.id is None:
            return

        # Cancel any existing pending builds
        if (task := self._pending_builds.pop(client.id, None)) is not None:
            task.cancel()

        self._pending_builds[client.id] = asyncio.create_task(
            self.trigger_build_after(uri, client.id, delay=2)
        )

    async def document_open(self, params: lsp.DidOpenTextDocumentParams):
        # Ensure that a Sphinx app instance is created the first time a document in a
        # given project is opened.
        if (uri := Uri.parse(params.text_document.uri)) is not None:
            await self.get_client(uri)

    async def document_save(self, params: lsp.DidSaveTextDocumentParams):
        if (uri := Uri.parse(params.text_document.uri)) is None:
            return

        client = await self.get_client(uri)
        if client is None or client.id is None:
            return

        # Cancel any existing pending builds
        if (task := self._pending_builds.pop(client.id, None)) is not None:
            task.cancel()

        await self.trigger_build(uri)

    async def trigger_build_after(self, uri: Uri, app_id: str, delay: float):
        """Trigger a build for the given uri after the given delay."""
        await asyncio.sleep(delay)

        self._pending_builds.pop(app_id)
        self.logger.debug("Triggering build")
        await self.trigger_build(uri)

    async def trigger_build(self, uri: Uri):
        """Trigger a build for the relevant Sphinx application for the given uri."""
        client = await self.get_client(uri)
        if client is None or client.building:
            return

        # Pass through any unsaved content to the Sphinx agent.
        content_overrides: Dict[str, str] = {}
        for src_uri in client.build_file_map.keys():
            doc = self.server.workspace.get_document(str(src_uri))
            doc_version = doc.version or 0
            saved_version = getattr(doc, "saved_version", 0)

            if saved_version < doc_version and (fs_path := src_uri.fs_path) is not None:
                content_overrides[fs_path] = doc.source

        result = await client.build(content_overrides=content_overrides)

        # Update diagnostics
        source = f"sphinx[{client.id}]"
        self.server.clear_diagnostics(source)
        for uri, items in client.diagnostics.items():
            diagnostics = [
                lsp.Diagnostic(
                    range=d.range,  # type: ignore[arg-type]
                    message=d.message,
                    source=source,
                    severity=d.severity,  # type: ignore[arg-type]
                )
                for d in items
            ]
            self.server.set_diagnostics(f"sphinx[{client.id}]", uri, diagnostics)

        self.server.sync_diagnostics()

        # Notify listeners.
        for listener in self.handlers.get("build", set()):
            try:
                # TODO: Concurrent awaiting?
                res = listener(client, result)
                if inspect.isawaitable(res):
                    await res
            except Exception:
                name = f"{listener}"
                self.logger.error("Error in build handler '%s'", name, exc_info=True)

    async def get_client(self, uri: Uri) -> Optional[SphinxClient]:
        """Given a uri, return the relevant sphinx client instance for it."""

        # Wait until the new client is created - it might be the one we're looking for!
        if self._client_creating:
            await self._client_creating

        # Always check the fully resolved uri.
        resolved_uri = uri.resolve()

        for src_uri, client in self.clients.items():
            if resolved_uri in client.build_file_map:
                return client

            # For now assume a single client instance per srcdir.
            # This *should* prevent us from spwaning endless client instances
            # when given a file located near a valid Sphinx project - but not actually
            # part of it.
            in_src_dir = str(resolved_uri).startswith(str(src_uri))
            if in_src_dir:
                # Of course, we can only tell if a uri truly is not in a project
                # when the build file map is populated!
                if len(client.build_file_map) == 0:
                    return client

                return None

        # Create a new client instance.
        self._client_creating = asyncio.create_task(self._create_client(uri))
        return await self._client_creating

    async def _create_client(self, uri: Uri) -> Optional[SphinxClient]:
        """Create a new sphinx client instance."""
        config = await self.server.get_user_config(
            "esbonio.sphinx", SphinxConfig, scope=uri
        )
        if config is None:
            return None

        resolved = config.resolve(uri, self.server.workspace, self.logger)
        if resolved is None:
            return None

        client = self.client_factory(self)
        await client.start(resolved)

        sphinx_info = await client.create_application(resolved)

        if client.src_uri is None:
            self.logger.error("No src uri!")
            await client.stop()
            return None

        self.server.lsp.notify("sphinx/appCreated", sphinx_info)
        self.clients[client.src_uri] = client
        return client
