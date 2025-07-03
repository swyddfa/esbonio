from __future__ import annotations

import asyncio
import traceback
import typing
import uuid
from functools import partial
from typing import Union

import attrs
import lsprotocol.types as lsp

from esbonio import server
from esbonio.server import Uri
from esbonio.sphinx_agent import types

from .client import ClientState
from .config import SphinxConfig

if typing.TYPE_CHECKING:
    from typing import Callable

    from esbonio.server.features.project_manager import ProjectManager

    from .client import SphinxClient

    SphinxClientFactory = Callable[["SphinxManager", "SphinxConfig"], "SphinxClient"]


@attrs.define
class ClientCreatedNotification:
    """The payload of a ``sphinx/clientCreated`` notification"""

    id: str
    """The client's id"""

    scope: str
    """The scope at which the client was created."""

    config: SphinxConfig
    """The final configuration."""


@attrs.define
class AppCreatedNotification:
    """The payload of a ``sphinx/appCreated`` notification"""

    id: str
    """The client's id"""

    application: types.SphinxInfo
    """Details about the created application."""


@attrs.define
class ClientErroredNotification:
    """The payload of a ``sphinx/clientErrored`` notification"""

    id: str
    """The client's id"""

    error: str
    """Short description of the error."""

    detail: str
    """Detailed description of the error."""


@attrs.define
class ClientDestroyedNotification:
    """The payload of ``sphinx/clientDestroyed`` notification."""

    id: str
    """The client's id"""


@attrs.define
class SphinxBuildTriggers:
    """Valid configuration options for Sphinx build triggers."""

    on_save: bool = attrs.field(default=True)
    """Trigger a build when a file is saved."""

    on_change: Union[bool, float] = attrs.field(default=2.0)
    """Trigger a build each time a file has changed, with a configurable delay."""


@attrs.define
class ManagerConfig:
    """Configuration options for the sphinx manager."""

    build_triggers: SphinxBuildTriggers = attrs.field(factory=SphinxBuildTriggers)
    """Options controlling when to trigger a Sphinx build."""


@attrs.define
class RestartSphinxParams:
    """Parameters for the ``esbonio.sphinx.restart`` command"""

    id: str
    """The id of the sphinx client to restart"""


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

        self.clients: dict[str, SphinxClient | None] = {
            # Prevent any clients from being created in the global scope.
            "": None,
        }
        """Holds currently active Sphinx clients."""

        self.config: ManagerConfig = ManagerConfig()
        """The SphinxManager's configuration."""

        self._events = server.EventSource(self.logger)
        """The SphinxManager can emit events."""

        self._pending_builds: dict[str, asyncio.Task] = {}
        """Holds tasks that will trigger a build after a given delay if not cancelled."""

        self._progress_tokens: dict[str, str] = {}
        """Holds work done progress tokens."""

    def add_listener(self, event: str, handler):
        self._events.add_listener(event, handler)

    def initialized(self, params: lsp.InitializedParams):
        """Called once the initial handshake between client and server has finished."""

        self.server.converter.register_structure_hook(
            Union[bool, float], lambda obj, _: obj
        )
        self.configuration.subscribe(
            "esbonio.sphinx", ManagerConfig, self.update_configuration
        )

    def update_configuration(self, event: server.ConfigChangeEvent[ManagerConfig]):
        """Called when the user's configuration is updated."""
        self.config = event.value

    async def document_change(self, params: lsp.DidChangeTextDocumentParams):
        if (uri := Uri.parse(params.text_document.uri)) is None:
            return

        client = await self.get_client(uri)
        if client is None:
            return

        if (delay := self.config.build_triggers.on_change) is False:
            return

        # Cancel any existing pending builds
        if (task := self._pending_builds.pop(client.id, None)) is not None:
            task.cancel()

        self._pending_builds[client.id] = asyncio.create_task(
            self.trigger_build_after(
                uri,
                client.id,
                delay=max(float(delay), 1.0),  # Enforce a minimum 1s delay
            )
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

        if not self.config.build_triggers.on_save:
            return

        # Cancel any existing pending builds
        if (task := self._pending_builds.pop(client.id, None)) is not None:
            task.cancel()

        self.logger.debug("Build triggered on save")
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
        self.logger.debug("Build triggered after %ss delay", delay)
        await self.trigger_build(uri)

    async def trigger_build(self, uri: Uri):
        """Trigger a build for the relevant Sphinx application for the given uri."""

        client = await self.get_client(uri)
        if client is None:
            return

        if client.state not in {ClientState.Running}:
            self.logger.debug("Skipping build, client is %s", client.state)
            return

        if (project := self.project_manager.get_project(uri)) is None:
            self.logger.debug("Skipping build, project is None")
            return

        # Pass through any unsaved content to the Sphinx agent.
        content_overrides: dict[str, str] = {}
        known_src_uris = await project.get_src_uris()

        for src_uri in known_src_uris:
            doc = self.server.workspace.get_text_document(str(src_uri))
            doc_version = doc.version or 0
            saved_version = getattr(doc, "saved_version", 0)

            if saved_version < doc_version:
                content_overrides[str(src_uri)] = doc.source

        try:
            result = await client.build(content_overrides=content_overrides)

            # Notify listeners.
            self._events.trigger("build", client, result)

        except Exception as exc:
            self.server.window_show_message(
                lsp.ShowMessageParams(message=f"{exc}", type=lsp.MessageType.Error)
            )
            return

    async def restart_client(self, client_id: str):
        """Restart the client with the given id"""
        for client in self.clients.values():
            if client is None:
                continue

            if client.id != client_id:
                continue

            try:
                await client.restart()
            except Exception:
                self.logger.exception("Unable to restart sphinx client")

            break

        else:
            self.logger.error(f"No client with id {client_id!r} available to restart")

    async def get_client(self, uri: Uri) -> SphinxClient | None:
        """Given a uri, return the relevant sphinx client instance for it."""

        scope = self.server.configuration.scope_for(uri)
        if scope not in self.clients:
            self.logger.debug("No client found, creating new subscription")
            self.server.configuration.subscribe(
                "esbonio.sphinx",
                SphinxConfig,
                partial(self._create_or_replace_client, uri),
                scope=uri,
            )

            # It's possible for this code path to be hit multiple times in quick
            # succession e.g. on a fresh server start with N .rst files already open,
            # creating the opportunity to accidentally spawn N duplicated clients!
            #
            # To prevent this, store a `None` at this scope, all being well it will be
            # replaced with the actual client instance when the
            # `_create_or_replace_client` callback runs.
            self.clients[scope] = None

            # The first few callers in a given scope will miss out, but that shouldn't
            # matter too much
            return None

        if (client := self.clients[scope]) is None:
            self.logger.debug("No applicable client for uri: %s", uri)
            return None

        return await client

    async def _create_or_replace_client(
        self, uri: Uri, event: server.ConfigChangeEvent[SphinxConfig]
    ):
        """Create or replace thesphinx client instance for the given config.

        Parameters
        ----------
        uri
           The uri for which the sphinx client was originally created for

        event
           The configuration change event
        """

        config = event.value

        # Do not try and create clients in the global scope
        if event.scope == "":
            return

        # If there was a previous client, stop it.
        if (previous_client := self.clients.pop(event.scope, None)) is not None:
            self.server.protocol.notify(
                "sphinx/clientDestroyed",
                ClientDestroyedNotification(id=previous_client.id),
            )
            self.server.run_task(previous_client.stop())

        resolved = config.resolve(uri, self.server.workspace, self.logger)
        if resolved is None:
            self.clients[event.scope] = None
            return

        self.clients[event.scope] = client = self.client_factory(self, resolved)
        client.add_listener("state-change", partial(self._on_state_change, event.scope))

        self.server.protocol.notify(
            "sphinx/clientCreated",
            ClientCreatedNotification(id=client.id, scope=event.scope, config=resolved),
        )
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
                self._events.trigger("app-created", client)
                self.server.protocol.notify(
                    "sphinx/appCreated",
                    AppCreatedNotification(id=client.id, application=sphinx_info),
                )

        if old_state == ClientState.Building:
            self.stop_progress(client)

        if new_state == ClientState.Building:
            self.server.run_task(self.start_progress(client))

        if new_state == ClientState.Errored:
            error = ""
            detail = ""

            if (exc := getattr(client, "exception", None)) is not None:
                error = f"{type(exc).__name__}: {exc}"
                detail = "".join(
                    traceback.format_exception(type(exc), exc, exc.__traceback__)
                )

            self.server.window_show_message(
                lsp.ShowMessageParams(message=error, type=lsp.MessageType.Error)
            )
            self.server.protocol.notify(
                "sphinx/clientErrored",
                ClientErroredNotification(id=client.id, error=error, detail=detail),
            )

    async def start_progress(self, client: SphinxClient):
        """Start reporting work done progress for the given client."""

        # Make sure any existing progress tokens are cleaned up
        if (existing := self._progress_tokens.get(client.id)) is not None:
            self.logger.warning("Overwriting existing progress token: %r!", existing)
            self.stop_progress(client)

        token = str(uuid.uuid4())
        self.logger.debug("Starting progress: '%s'", token)

        try:
            await self.server.work_done_progress.create_async(token)
        except Exception as exc:
            self.logger.debug("Unable to create progress token: %s", exc)
            return

        self._progress_tokens[client.id] = token
        self.server.work_done_progress.begin(
            token,
            lsp.WorkDoneProgressBegin(title="sphinx-build", cancellable=False),
        )

    def stop_progress(self, client: SphinxClient):
        if (token := self._progress_tokens.pop(client.id, None)) is None:
            return

        self.logger.debug("Ending progress: %r", token)
        self.server.work_done_progress.end(
            token, lsp.WorkDoneProgressEnd(message="Finished")
        )

    def report_progress(self, client: SphinxClient, progress: types.ProgressParams):
        """Report progress done for the given client."""

        if client.state not in {ClientState.Running, ClientState.Building}:
            return

        if (token := self._progress_tokens.get(client.id, None)) is None:
            return

        self.server.work_done_progress.report(
            token,
            lsp.WorkDoneProgressReport(
                message=progress.message,
                percentage=progress.percentage,
                cancellable=False,
            ),
        )
