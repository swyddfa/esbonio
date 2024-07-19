from __future__ import annotations

import asyncio
import collections
import inspect
import logging
import platform
import traceback
import typing
from typing import TypeVar
from uuid import uuid4

import cattrs
from lsprotocol import types
from pygls.capabilities import get_capability
from pygls.server import LanguageServer
from pygls.workspace import TextDocument
from pygls.workspace import Workspace

from . import Uri
from ._configuration import Configuration

if typing.TYPE_CHECKING:
    from typing import Any
    from typing import Callable
    from typing import Coroutine
    from typing import Dict
    from typing import List
    from typing import Optional
    from typing import Set
    from typing import Tuple
    from typing import Type

    from .feature import LanguageFeature

__version__ = "1.0.0b6"
T = TypeVar("T")
LF = TypeVar("LF", bound="LanguageFeature")


class EsbonioWorkspace(Workspace):
    """A modified version of pygls' workspace that ensures uris are always resolved."""

    def get_document(self, doc_uri: str) -> TextDocument:
        uri = str(Uri.parse(doc_uri).resolve())
        return super().get_text_document(uri)

    def put_document(self, text_document: types.TextDocumentItem):
        text_document.uri = str(Uri.parse(text_document.uri).resolve())
        return super().put_text_document(text_document)

    def remove_document(self, doc_uri: str):
        doc_uri = str(Uri.parse(doc_uri).resolve())
        return super().remove_text_document(doc_uri)

    def update_document(
        self,
        text_doc: types.VersionedTextDocumentIdentifier,
        change: types.TextDocumentContentChangeEvent,
    ):
        text_doc.uri = str(Uri.parse(text_doc.uri).resolve())
        return super().update_text_document(text_doc, change)


class EsbonioLanguageServer(LanguageServer):
    """The Esbonio language server"""

    def __init__(self, logger: Optional[logging.Logger] = None, *args, **kwargs):
        if "name" not in kwargs:
            kwargs["name"] = "esbonio"

        if "version" not in kwargs:
            kwargs["version"] = __version__

        super().__init__(*args, **kwargs)

        self._diagnostics: Dict[Tuple[str, Uri], List[types.Diagnostic]] = {}
        """Where we store and manage diagnostics."""

        self._loaded_extensions: Dict[str, Any] = {}
        """Record of server modules that have been loaded."""

        self._features: Dict[Type[LanguageFeature], LanguageFeature] = {}
        """The collection of language features registered with the server."""

        self._ready: asyncio.Future[bool] = asyncio.Future()
        """Indicates if the server is ready."""

        self._tasks: Set[asyncio.Task] = set()
        """Used to hold running tasks"""

        self.logger = logger or logging.getLogger(__name__)
        """The logger instance to use."""

        self.configuration = Configuration(self)
        """Manages the fetching of configuration values."""

    def __iter__(self):
        return iter(self._features.items())

    @property
    def ready(self) -> asyncio.Future:
        return self._ready

    @property
    def converter(self) -> cattrs.Converter:
        """The cattrs converter instance we should use."""
        return self.lsp._converter

    def _finish_task(self, task: asyncio.Task[Any]):
        """Cleanup a finished task."""
        self.logger.debug("Task finished: %s", task)
        self._tasks.discard(task)

        if (exc := task.exception()) is not None:
            self.logger.error(
                "Error in async task\n%s",
                traceback.format_exception(type(exc), exc, exc.__traceback__),
            )

    def run_task(self, coro: Coroutine, *, name: Optional[str] = None) -> asyncio.Task:
        """Convert a given coroutine into a task and ensure it is executed."""

        task = asyncio.create_task(coro, name=name)
        self.logger.debug("Scheduled task: %s", task)
        task.add_done_callback(self._finish_task)

        self._tasks.add(task)
        return task

    def initialize(self, params: types.InitializeParams):
        self.logger.info(
            "Initialising esbonio v%s, using Python v%s on %s",
            __version__,
            platform.python_version(),
            platform.platform(aliased=True, terse=True),
        )
        if (client := params.client_info) is not None:
            self.logger.info("Language client: %s %s", client.name, client.version)

        # TODO: Propose patch to pygls for providing custom Workspace implementations.
        self.lsp._workspace = EsbonioWorkspace(
            self.workspace.root_uri,
            self.workspace._sync_kind,
            list(self.workspace.folders.values()),
        )

        self.configuration.initialization_options = params.initialization_options

    async def initialized(self, params: types.InitializedParams):
        self.configuration.update_file_configuration()

        await asyncio.gather(
            self.configuration.update_workspace_configuration(),
            self._register_did_change_configuration_handler(),
            self._register_did_change_watched_files_handler(),
        )
        self._ready.set_result(True)

    def lsp_shutdown(self, params: None):
        """Called when the server is instructed to ``shutdown`` by the client."""

    def load_extension(self, name: str, setup: Callable):
        """Load the given setup function as an extension.

        If an extension with the given ``name`` already exists, the given setup function
        will be ignored.

        The ``setup`` function can declare dependencies in the form of type
        annotations.

        .. code-block:: python

           from esbonio.lsp.roles import Roles
           from esbonio.lsp.sphinx import SphinxLanguageServer


           def esbonio_setup(rst: SphinxLanguageServer, roles: Roles): ...

        In this example the setup function is requesting instances of the
        :class:`~esbonio.lsp.sphinx.SphinxLanguageServer` and the
        :class:`~esbonio.lsp.roles.Roles` language feature.

        Parameters
        ----------
        name
           The name to give the extension

        setup
           The setup function to call
        """

        if name in self._loaded_extensions:
            self.logger.debug("Skipping extension '%s', already loaded", name)
            return

        arguments = _get_setup_arguments(self, setup, name)
        if not arguments:
            return

        try:
            setup(**arguments)

            self.logger.debug("Loaded extension '%s'", name)
            self._loaded_extensions[name] = setup
        except Exception:
            self.logger.error("Unable to load extension '%s'", name, exc_info=True)

    def add_feature(self, feature: LanguageFeature):
        """Register a language feature with the server.

        Parameters
        ----------
        feature
           The language feature
        """
        feature_cls = type(feature)
        if feature_cls in self._features:
            name = f"{feature_cls.__module__}.{feature_cls.__name__}"
            raise RuntimeError(f"Feature '{name}' has already been registered")

        self._features[feature_cls] = feature

    def get_feature(self, feature_cls: Type[LF]) -> Optional[LF]:
        """Returns the requested language feature if it exists, otherwise it returns
        ``None``.

        Parameters
        ----------
        feature_cls
           The class definiion of the feature to retrieve
        """
        return self._features.get(feature_cls, None)  # type: ignore

    def clear_diagnostics(self, source: str, uri: Optional[Uri] = None) -> None:
        """Clear diagnostics from the given source.

        Parameters
        ----------
        source:
           The source from which to clear diagnostics.
        uri:
           If given, clear diagnostics from within just this uri. Otherwise, all
           diagnostics from the given source are cleared.
        """

        for key in self._diagnostics.keys():
            clear_source = source == key[0]
            clear_uri = uri == key[1] or uri is None

            if clear_source and clear_uri:
                self._diagnostics[key] = []

    def add_diagnostics(self, source: str, uri: Uri, diagnostic: types.Diagnostic):
        """Add a diagnostic to the given source and uri.

        Parameters
        ----------
        source
           The source the diagnostics are from
        uri
           The uri the diagnostics are associated with
        diagnostic
           The diagnostic to add
        """
        key = (source, uri)
        self._diagnostics.setdefault(key, []).append(diagnostic)

    def set_diagnostics(
        self, source: str, uri: Uri, diagnostics: List[types.Diagnostic]
    ) -> None:
        """Set the diagnostics for the given source and uri.

        Parameters
        ----------
        source:
           The source the diagnostics are from
        uri:
           The uri the diagnostics are associated with
        diagnostics:
           The diagnostics themselves
        """
        self._diagnostics[(source, uri)] = diagnostics

    def get_language_at(self, document: TextDocument, position: types.Position) -> str:
        """Return the language at the given location"""
        language = document.language_id

        if language in {"rst", "restructuredtext"}:
            return "rst"

        if language in {"markdown"}:
            return "markdown"

        return ""

    def sync_diagnostics(self) -> None:
        """Update the client with the currently stored diagnostics.

        When the client supports the pull diagnostics model, this is a no-op.
        """
        pull_support = get_capability(
            self.client_capabilities, "text_document.diagnostic", None
        )
        if pull_support is not None:
            return

        uris = {uri for _, uri in self._diagnostics.keys()}
        diagnostics = {uri: DiagnosticList() for uri in uris}

        for (_, uri), diags in self._diagnostics.items():
            diagnostics[uri].extend(diags)

        for uri, diag_list in diagnostics.items():
            self.logger.debug("Publishing %d diagnostics for: %s", len(diag_list), uri)
            self.publish_diagnostics(str(uri), diag_list.data)

    async def _register_did_change_watched_files_handler(self):
        """Register the server's handler for ``workspace/didChangeWatchedFiles``."""
        capabilities = self.client_capabilities
        registration_supported = get_capability(
            capabilities,
            "workspace.did_change_watched_files.dynamic_registration",
            False,
        )
        if not registration_supported:
            self.logger.info(
                "Client does not support dynamic registration of '%s' handlers, "
                "server might not be able to react to configuration changes.",
                types.WORKSPACE_DID_CHANGE_WATCHED_FILES,
            )
            return

        try:
            await self.register_capability_async(
                types.RegistrationParams(
                    registrations=[
                        types.Registration(
                            id=str(uuid4()),
                            method=types.WORKSPACE_DID_CHANGE_WATCHED_FILES,
                            register_options=types.DidChangeWatchedFilesRegistrationOptions(
                                watchers=[
                                    types.FileSystemWatcher(
                                        glob_pattern="**/pyproject.toml"
                                    )
                                ]
                            ),
                        ),
                    ]
                )
            )
            self.logger.debug(
                "Registered '%s' handler", types.WORKSPACE_DID_CHANGE_WATCHED_FILES
            )
        except Exception:
            self.logger.error(
                "Unable to register '%s' handler",
                types.WORKSPACE_DID_CHANGE_WATCHED_FILES,
                exc_info=True,
            )

    async def _register_did_change_configuration_handler(self):
        """Register the server's handler for ``workspace/didChangeConfiguration``.

        The spec says that in order to receive these notifications we need to
        dynamically register our capability to process them. (Though I think some
        editors send them regardless.)
        """
        capabilities = self.client_capabilities
        registration_supported = get_capability(
            capabilities,
            "workspace.did_change_configuration.dynamic_registration",
            False,
        )
        if not registration_supported:
            self.logger.info(
                "Client does not support dynamic registration of '%s' handlers, "
                "server might not be able to react to configuration changes.",
                types.WORKSPACE_DID_CHANGE_CONFIGURATION,
            )
            return

        try:
            await self.register_capability_async(
                types.RegistrationParams(
                    registrations=[
                        types.Registration(
                            id=str(uuid4()),
                            method=types.WORKSPACE_DID_CHANGE_CONFIGURATION,
                        ),
                    ]
                )
            )
            self.logger.debug(
                "Registered '%s' handler", types.WORKSPACE_DID_CHANGE_CONFIGURATION
            )
        except Exception:
            self.logger.error(
                "Unable to register '%s' handler",
                types.WORKSPACE_DID_CHANGE_CONFIGURATION,
                exc_info=True,
            )


class DiagnosticList(collections.UserList):
    """A list type dedicated to holding diagnostics.

    This is mainly to ensure that only one instance of a diagnostic ever gets
    reported.
    """

    def append(self, item: types.Diagnostic):
        if not isinstance(item, types.Diagnostic):
            raise TypeError("Expected Diagnostic")

        for existing in self.data:
            fields = [
                existing.range == item.range,
                existing.message == item.message,
                existing.severity == item.severity,
                existing.code == item.code,
                existing.source == item.source,
            ]

            if all(fields):
                # Item already added, nothing to do.
                return

        self.data.append(item)


def _get_setup_arguments(
    server: EsbonioLanguageServer, setup: Callable, modname: str
) -> Optional[Dict[str, Any]]:
    """Given a setup function, try to construct the collection of arguments to pass to
    it.
    """
    annotations = typing.get_type_hints(setup)
    parameters = {
        p.name: annotations[p.name]
        for p in inspect.signature(setup).parameters.values()
    }

    args = {}
    for name, type_ in parameters.items():
        if issubclass(server.__class__, type_):
            args[name] = server
            continue

        from .feature import LanguageFeature

        if issubclass(type_, LanguageFeature):
            # Try and obtain an instance of the requested language feature.
            feature = server.get_feature(type_)
            if feature is not None:
                args[name] = feature
                continue

            server.logger.debug(
                "Skipping extension '%s', server missing requested feature: '%s'",
                modname,
                type_,
            )
            return None

        server.logger.error(
            "Skipping extension '%s', parameter '%s' has unsupported type: '%s'",
            modname,
            name,
            type_,
        )
        return None

    return args
