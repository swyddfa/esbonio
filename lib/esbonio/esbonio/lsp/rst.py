import collections
import importlib
import logging
import typing
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

import pygls.uris as Uri
from docutils.parsers.rst import Directive
from docutils.parsers.rst import directives
from docutils.parsers.rst import roles
from pydantic import BaseModel
from pydantic import Field
from pygls import IS_WIN
from pygls.lsp.types import Diagnostic
from pygls.lsp.types import DidSaveTextDocumentParams
from pygls.lsp.types import InitializedParams
from pygls.lsp.types import InitializeParams
from pygls.lsp.types import Position
from pygls.server import LanguageServer
from pygls.workspace import Document

from .log import LOG_LEVELS
from .log import LogFilter
from .log import LspHandler

if typing.TYPE_CHECKING:
    from .feature import LanguageFeature


class DiagnosticList(collections.UserList):
    """A list type dedicated to holding diagnostics.

    This is mainly to ensure that only one instance of a diagnostic ever gets
    reported.
    """

    def append(self, item: Diagnostic):

        if not isinstance(item, Diagnostic):
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


class ServerConfig(BaseModel):
    """Configuration options for the server."""

    log_level: Optional[str] = Field("error", alias="logLevel")
    """The logging level of server messages to display."""

    log_filter: Optional[List[str]] = Field(None, alias="logFilter")
    """A list of logger names to restrict output to."""


class InitializationOptions(BaseModel):
    """The initialization options we can expect to receive from a client."""

    server: Optional[ServerConfig] = Field(default_factory=ServerConfig)
    """The ``esbonio.server.*`` namespace of options."""


class RstLanguageServer(LanguageServer):
    """A generic reStructuredText language server."""

    def __init__(self, logger: Optional[logging.Logger] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.logger = logger or logging.getLogger(__name__)
        """The base logger that should be used for all language sever log entries."""

        self.user_config: Optional[BaseModel] = None
        """The user's configuration."""

        self._diagnostics: Dict[Tuple[str, str], List[Diagnostic]] = {}
        """Where we store and manage diagnostics."""

        self._features: Dict[str, LanguageFeature] = {}
        """The list of language features registered with the server."""

        self._directives: Optional[Dict[str, Directive]] = None
        """Cache for known directives."""

        self._roles: Optional[Dict[str, Any]] = None
        """Cache for known roles."""

    @property
    def configuration(self) -> Dict[str, Any]:
        """Return the server's actual configuration."""
        return self.user_config.dict()

    def initialize(self, params: InitializeParams):
        self.user_config = InitializationOptions(**params.initialization_options)
        self._configure_logging(self.user_config.server)

    def initialized(self, params: InitializedParams):
        pass

    def save(self, params: DidSaveTextDocumentParams):
        pass

    def add_feature(self, feature: "LanguageFeature"):
        """Register a language feature with the server."""

        key = feature.__class__.__name__.lower()
        self._features[key] = feature

    def get_feature(self, key) -> Optional["LanguageFeature"]:
        return self._features.get(key, None)

    def get_directives(self) -> Dict[str, Directive]:
        """Return a dictionary of the known directives"""

        if self._directives is not None:
            return self._directives

        ignored_directives = ["restructuredtext-test-directive"]
        found_directives = {**directives._directive_registry, **directives._directives}

        self._directives = {
            k: resolve_directive(v)
            for k, v in found_directives.items()
            if k not in ignored_directives
        }

        return self._directives

    def get_roles(self) -> Dict[str, Any]:
        """Return a dictionary of known roles."""

        if self._roles is not None:
            return self._roles

        found_roles = {**roles._roles, **roles._role_registry}

        self._roles = {
            k: v for k, v in found_roles.items() if v != roles.unimplemented_role
        }

        return self._roles

    def clear_diagnostics(self, source: str, uri: Optional[str] = None) -> None:
        """Clear diagnostics from the given source.

        Parameters
        ----------
        source:
           The source from which to clear diagnostics.
        uri:
           If given, clear diagnostics from within just this uri. Otherwise, all
           diagnostics from the given source are cleared.
        """

        uri = normalise_uri(uri)

        for key in self._diagnostics.keys():
            clear_source = source == key[0]
            clear_uri = uri == key[1] or uri is None

            if clear_source and clear_uri:
                self._diagnostics[key] = []

    def set_diagnostics(
        self, source: str, uri: str, diagnostics: List[Diagnostic]
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
        uri = normalise_uri(uri)
        self._diagnostics[(source, uri)] = diagnostics

    def sync_diagnostics(self) -> None:
        """Update the client with the currently stored diagnostics."""

        uris = {uri for _, uri in self._diagnostics.keys()}
        diagnostics = {uri: DiagnosticList() for uri in uris}

        for (source, uri), diags in self._diagnostics.items():
            for diag in diags:
                diag.source = source
                diagnostics[uri].append(diag)

        for uri, diags in diagnostics.items():
            self.logger.debug("Publishing %d diagnostics for: %s", len(diags), uri)
            self.publish_diagnostics(uri, diags.data)

    def line_to_position(self, doc: Document, position: Position) -> str:
        """Return the contents of the line up until the given position."""

        try:
            line = doc.lines[position.line]
        except IndexError:
            return ""

        return line[: position.character]

    def _configure_logging(self, config: ServerConfig):

        level = LOG_LEVELS[config.log_level]

        lsp_logger = logging.getLogger("esbonio.lsp")
        lsp_logger.setLevel(level)

        lsp_handler = LspHandler(self)
        lsp_handler.setLevel(level)

        if config.log_filter is not None and len(config.log_filter) > 0:
            lsp_handler.addFilter(LogFilter(config.log_filter))

        formatter = logging.Formatter("[%(name)s] %(message)s")
        lsp_handler.setFormatter(formatter)
        lsp_logger.addHandler(lsp_handler)


def resolve_directive(directive: Union[Directive, Tuple[str]]) -> Directive:
    """Return the directive based on the given reference.

    'Core' docutils directives are returned as tuples ``(modulename, ClassName)``
    so they need to be resolved manually.
    """

    if isinstance(directive, tuple):
        mod, cls = directive

        modulename = "docutils.parsers.rst.directives.{}".format(mod)
        module = importlib.import_module(modulename)
        directive = getattr(module, cls)

    return directive


def normalise_uri(uri: Optional[str]) -> Optional[str]:

    if uri:
        uri = Uri.from_fs_path(Uri.to_fs_path(uri))

        # Paths on windows are case insensitive.
        if IS_WIN:
            uri = uri.lower()

    return uri
