from __future__ import annotations

import asyncio
import sys
import typing
import uuid
from typing import Callable
from typing import Dict
from typing import Optional

import lsprotocol.types as lsp

import esbonio.sphinx_agent.types as types
from esbonio.server import EventSource
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

        self._events = EventSource(self.logger)
        """The SphinxManager can emit events."""

        self._pending_builds: Dict[str, asyncio.Task] = {}
        """Holds tasks that will trigger a build after a given delay if not cancelled."""

        self._client_creating: Optional[asyncio.Task] = None
        """If set, indicates we're in the process of setting up a new client."""

        self._progress_tokens: Dict[str, str] = {}
        """Holds work done progress tokens."""

    def add_listener(self, event: str, handler):
        self._events.add_listener(event, handler)

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

    async def shutdown(self, params: None):
        """Called when the server is instructed to ``shutdown``."""

        # Stop creating any new clients.
        if self._client_creating and not self._client_creating.done():
            args = {}
            if sys.version_info.minor > 8:
                args["msg"] = "Server is shutting down"

            self.logger.debug("Aborting client creation")
            self._client_creating.cancel(**args)

        # Stop any existing clients.
        tasks = []
        for client in self.clients.values():
            self.logger.debug("Stopping SphinxClient: %s", client)
            tasks.append(asyncio.create_task(client.stop()))

        await asyncio.gather(*tasks)

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
        known_src_uris = await client.get_src_uris()

        for src_uri in known_src_uris:
            doc = self.server.workspace.get_document(str(src_uri))
            doc_version = doc.version or 0
            saved_version = getattr(doc, "saved_version", 0)

            if saved_version < doc_version and (fs_path := src_uri.fs_path) is not None:
                content_overrides[fs_path] = doc.source

        await self.start_progress(client)

        try:
            result = await client.build(content_overrides=content_overrides)
        except Exception as exc:
            self.server.show_message(f"{exc}", lsp.MessageType.Error)
            return
        finally:
            self.stop_progress(client)

        # Notify listeners.
        self._events.trigger("build", client, result)

    async def get_client(self, uri: Uri) -> Optional[SphinxClient]:
        """Given a uri, return the relevant sphinx client instance for it."""

        # Wait until the new client is created - it might be the one we're looking for!
        if self._client_creating:
            await self._client_creating

        # Always check the fully resolved uri.
        resolved_uri = uri.resolve()

        for src_uri, client in self.clients.items():
            if resolved_uri in (await client.get_src_uris()):
                return client

            # For now assume a single client instance per srcdir.
            # This *should* prevent us from spwaning endless client instances
            # when given a file located near a valid Sphinx project - but not actually
            # part of it.
            in_src_dir = str(resolved_uri).startswith(str(src_uri))
            if in_src_dir:
                # Of course, we can only tell if a uri truly is not in a project
                # when the build file map is populated!
                # if len(client.build_file_map) == 0:
                return client

        # Create a new client instance.
        self._client_creating = asyncio.create_task(self._create_client(uri))
        try:
            return await self._client_creating
        finally:
            # Be sure to unset the task when it resolves
            self._client_creating = None

    async def _create_client(self, uri: Uri) -> Optional[SphinxClient]:
        """Create a new sphinx client instance."""
        # TODO: Replace with config subscription
        await self.server.ready
        config = self.server.configuration.get(
            "esbonio.sphinx", SphinxConfig, scope=uri
        )
        if config is None:
            return None

        resolved = config.resolve(uri, self.server.workspace, self.logger)
        if resolved is None:
            return None

        client = self.client_factory(self)

        try:
            await client.start(resolved)
        except Exception as exc:
            message = "Unable to start sphinx-agent"
            self.logger.error(message, exc_info=True)
            self.server.show_message(f"{message}: {exc}", lsp.MessageType.Error)

            return None

        try:
            sphinx_info = await client.create_application(resolved)
        except Exception as exc:
            message = "Unable to create sphinx application"
            self.logger.error(message, exc_info=True)
            self.server.show_message(f"{message}: {exc}", lsp.MessageType.Error)

            await client.stop()
            return None

        if client.src_uri is None:
            self.logger.error("No src uri!")
            await client.stop()
            return None

        self.server.lsp.notify("sphinx/appCreated", sphinx_info)
        self.clients[client.src_uri] = client
        return client

    async def start_progress(self, client: SphinxClient):
        """Start reporting work done progress for the given client."""

        if client.id is None:
            return

        token = str(uuid.uuid4())
        self.logger.debug("Starting progress: '%s'", token)

        try:
            await self.server.progress.create_async(token)
        except Exception as exc:
            self.logger.debug("Unable to create progress token: %s", exc)
            return

        self._progress_tokens[client.id] = token
        self.server.progress.begin(
            token,
            lsp.WorkDoneProgressBegin(title="sphinx-build", cancellable=False),
        )

    def stop_progress(self, client: SphinxClient):
        if client.id is None:
            return

        if (token := self._progress_tokens.pop(client.id, None)) is None:
            return

        self.server.progress.end(token, lsp.WorkDoneProgressEnd(message="Finished"))

    def report_progress(self, client: SphinxClient, progress: types.ProgressParams):
        """Report progress done for the given client."""

        if client.id is None:
            return

        if (token := self._progress_tokens.get(client.id, None)) is None:
            return

        self.server.progress.report(
            token,
            lsp.WorkDoneProgressReport(
                message=progress.message,
                percentage=progress.percentage,
                cancellable=False,
            ),
        )
