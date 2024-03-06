from __future__ import annotations

import asyncio
import typing
import uuid
from functools import partial

import lsprotocol.types as lsp

from esbonio import server
from esbonio.server import Uri
from esbonio.sphinx_agent import types

from .client import ClientState
from .config import SphinxConfig

if typing.TYPE_CHECKING:
    from typing import Callable
    from typing import Dict
    from typing import Optional

    from esbonio.server.features.project_manager import ProjectManager

    from .client import SphinxClient

    SphinxClientFactory = Callable[["SphinxManager", "SphinxConfig"], "SphinxClient"]


class SphinxManager(server.LanguageFeature):
    """Responsible for managing Sphinx application instances."""

    def __init__(
        self,
        client_factory: SphinxClientFactory,
        project_manager: ProjectManager,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.client_factory = client_factory
        """Used to create new Sphinx client instances."""

        self.project_manager = project_manager
        """The project manager instance to use."""

        self.clients: Dict[str, Optional[SphinxClient]] = {
            # Prevent any clients from being created in the global scope.
            "": None,
        }
        """Holds currently active Sphinx clients."""

        self._events = server.EventSource(self.logger)
        """The SphinxManager can emit events."""

        self._pending_builds: Dict[str, asyncio.Task] = {}
        """Holds tasks that will trigger a build after a given delay if not cancelled."""

        self._progress_tokens: Dict[str, str] = {}
        """Holds work done progress tokens."""

    def add_listener(self, event: str, handler):
        self._events.add_listener(event, handler)

    async def document_change(self, params: lsp.DidChangeTextDocumentParams):
        if (uri := Uri.parse(params.text_document.uri)) is None:
            return

        client = await self.get_client(uri)
        if client is None:
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
        if client is None:
            return

        # Cancel any existing pending builds
        if (task := self._pending_builds.pop(client.id, None)) is not None:
            task.cancel()

        await self.trigger_build(uri)

    async def shutdown(self, params: None):
        """Called when the server is instructed to ``shutdown``."""

        # Stop any existing clients.
        tasks = []
        for client in self.clients.values():
            if client:
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
        if client is None or client.state != ClientState.Running:
            return

        if (project := self.project_manager.get_project(uri)) is None:
            return

        # Pass through any unsaved content to the Sphinx agent.
        content_overrides: Dict[str, str] = {}
        known_src_uris = await project.get_src_uris()

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

        scope = self.server.configuration.scope_for(uri)
        if scope not in self.clients:
            self.logger.debug("No client found, creating new subscription")
            self.server.configuration.subscribe(
                "esbonio.sphinx",
                SphinxConfig,
                self._create_or_replace_client,
                scope=uri,
            )
            # The first few callers in a given scope will miss out, but that shouldn't matter
            # too much
            return None

        if (client := self.clients[scope]) is None:
            self.logger.debug("No applicable client for uri: %s", uri)
            return None

        return await client

    async def _create_or_replace_client(
        self, event: server.ConfigChangeEvent[SphinxConfig]
    ):
        """Create or replace thesphinx client instance for the given config."""

        config = event.value

        # Do not try and create clients in the global scope
        if event.scope == "":
            return

        # If there was a previous client, stop it.
        if (previous_client := self.clients.pop(event.scope, None)) is not None:
            self.server.run_task(previous_client.stop())

        resolved = config.resolve(
            Uri.parse(event.scope), self.server.workspace, self.logger
        )
        if resolved is None:
            self.clients[event.scope] = None
            return

        self.clients[event.scope] = client = self.client_factory(self, resolved)
        client.add_listener("state-change", partial(self._on_state_change, event.scope))

        self.server.lsp.notify("sphinx/clientCreated", resolved)
        self.logger.debug("Client created for scope %s", event.scope)

        # Start the client
        await client

    def _on_state_change(
        self,
        scope: str,
        client: SphinxClient,
        old_state: ClientState,
        new_state: ClientState,
    ):
        """React to state changes in the client."""

        if old_state == ClientState.Starting and new_state == ClientState.Running:
            if (sphinx_info := client.sphinx_info) is not None:
                self.project_manager.register_project(scope, client.db)
                self.server.lsp.notify("sphinx/appCreated", sphinx_info)

    async def start_progress(self, client: SphinxClient):
        """Start reporting work done progress for the given client."""

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
        if (token := self._progress_tokens.pop(client.id, None)) is None:
            return

        self.server.progress.end(token, lsp.WorkDoneProgressEnd(message="Finished"))

    def report_progress(self, client: SphinxClient, progress: types.ProgressParams):
        """Report progress done for the given client."""

        if client.state not in {ClientState.Running, ClientState.Building}:
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
