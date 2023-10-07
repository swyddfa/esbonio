from __future__ import annotations

import collections
import inspect
import json
import logging
import typing
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Type
from typing import TypeVar

import attrs
from lsprotocol import types
from pygls.server import LanguageServer
from pygls.workspace import Document
from pygls.workspace import Workspace

from ._uri import Uri
from .log import setup_logging

if typing.TYPE_CHECKING:
    from .feature import LanguageFeature

__version__ = "0.16.1"
T = TypeVar("T")
LF = TypeVar("LF", bound="LanguageFeature")


@attrs.define
class ServerConfig:
    """Configuration options for the server."""

    log_filter: List[str] = attrs.field(factory=list)
    """A list of logger names to restrict output to."""

    log_level: str = attrs.field(default="error")
    """The logging level of server messages to display."""

    show_deprecation_warnings: bool = attrs.field(default=False)
    """Developer flag to enable deprecation warnings."""


class EsbonioWorkspace(Workspace):
    """A modified version of pygls' workspace that ensures uris are always resolved."""

    def get_document(self, doc_uri: str) -> Document:
        uri = str(Uri.parse(doc_uri).resolve())
        return super().get_document(uri)

    def put_document(self, text_document: types.TextDocumentItem):
        text_document.uri = str(Uri.parse(text_document.uri).resolve())
        return super().put_document(text_document)

    def remove_document(self, doc_uri: str):
        doc_uri = str(Uri.parse(doc_uri).resolve())
        return super().remove_document(doc_uri)

    def update_document(
        self,
        text_doc: types.VersionedTextDocumentIdentifier,
        change: types.TextDocumentContentChangeEvent,
    ):
        text_doc.uri = str(Uri.parse(text_doc.uri).resolve())
        return super().update_document(text_doc, change)


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

        self.logger = logger or logging.getLogger(__name__)
        """The logger instance to use."""

        self.converter = self.lsp._converter
        """The cattrs converter instance we should use."""

        self.initialization_options: Optional[types.LSPAny] = None
        """The received initializaion options (if any)"""

    def __iter__(self):
        return iter(self._features.items())

    def initialize(self, params: types.InitializeParams):
        self.logger.info("Initialising esbonio v%s", __version__)
        if (client := params.client_info) is not None:
            self.logger.info("Language client: %s %s", client.name, client.version)

        # TODO: Propose patch to pygls for providing custom Workspace implementations.
        self.lsp._workspace = EsbonioWorkspace(
            self.workspace.root_uri,
            self.workspace._sync_kind,
            list(self.workspace.folders.values()),
        )

        self.initialization_options = params.initialization_options

        # TODO: Merge this with self.get_user_config somehow...
        server_config = ServerConfig()
        if self.initialization_options is not None:
            try:
                config = self.initialization_options.get("server", {})
                server_config = self.converter.structure(config, ServerConfig)
            except Exception:
                self.logger.error("Unable to parse server config", exc_info=True)

        setup_logging(self, server_config)

    def load_extension(self, name: str, setup: Callable):
        """Load the given setup function as an extension.

        If an extension with the given ``name`` already exists, the given setup function
        will be ignored.

        The ``setup`` function can declare dependencies in the form of type
        annotations.

        .. code-block:: python

           from esbonio.lsp.roles import Roles
           from esbonio.lsp.sphinx import SphinxLanguageServer

           def esbonio_setup(rst: SphinxLanguageServer, roles: Roles):
               ...

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

    async def get_user_config(
        self,
        section: str,
        spec: Type[T],
        scope: Optional[Uri] = None,
    ) -> Optional[T]:
        """Return the user's configuration for the given ``section``.

        Using a ``workspace/configuration`` request, ask the client for the user's
        configuration for the given ``section``.

        ``spec`` should be a class definition representing the expected "shape" of the
        result.

        Parameters
        ----------
        section
           The name of the configuration section to retrieve

        spec
           The class definition representing the expected result.

        scope
           An optional URI, useful in a multi-root context to select which root the
           configuration should be retrieved from.

        Returns
        -------
        T | None
           The user's configuration, parsed as an instance of ``T``.
           If ``None``, the config was not available / there was an error.
        """
        params = types.ConfigurationParams(
            items=[
                types.ConfigurationItem(
                    section=section, scope_uri=str(scope) if scope else None
                )
            ]
        )
        self.logger.debug(
            "workspace/configuration: %s",
            json.dumps(self.converter.unstructure(params), indent=2),
        )
        result = await self.get_configuration_async(params)

        try:
            self.logger.debug("configuration: %s", json.dumps(result[0], indent=2))
            return self.converter.structure(result[0], spec)
        except Exception:
            self.logger.error(
                "Unable to parse configuration as '%s'", spec.__name__, exc_info=True
            )
            return None

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

    def sync_diagnostics(self) -> None:
        """Update the client with the currently stored diagnostics."""

        uris = {uri for _, uri in self._diagnostics.keys()}
        diagnostics = {uri: DiagnosticList() for uri in uris}

        for (source, uri), diags in self._diagnostics.items():
            for diag in diags:
                diag.source = source
                diagnostics[uri].append(diag)

        for uri, diag_list in diagnostics.items():
            self.logger.debug("Publishing %d diagnostics for: %s", len(diag_list), uri)
            self.publish_diagnostics(str(uri), diag_list.data)


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

        from .feature import LanguageFeature  # noqa: F402

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
