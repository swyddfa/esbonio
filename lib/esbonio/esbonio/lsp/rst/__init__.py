import collections
import inspect
import logging
import pathlib
import re
import traceback
import typing
import warnings
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Type
from typing import TypeVar

import pygls.uris as Uri
from docutils.parsers.rst import Directive
from pydantic import BaseModel
from pydantic import Field
from pygls import IS_WIN
from pygls.lsp.types import ClientCapabilities
from pygls.lsp.types import CodeAction
from pygls.lsp.types import CodeActionParams
from pygls.lsp.types import CompletionItem
from pygls.lsp.types import CompletionItemTag
from pygls.lsp.types import DeleteFilesParams
from pygls.lsp.types import Diagnostic
from pygls.lsp.types import DidSaveTextDocumentParams
from pygls.lsp.types import DocumentLink
from pygls.lsp.types import InitializedParams
from pygls.lsp.types import InitializeParams
from pygls.lsp.types import Location
from pygls.lsp.types import MarkupKind
from pygls.lsp.types import Position
from pygls.server import LanguageServer
from pygls.workspace import Document

from esbonio.cli import setup_cli
from esbonio.lsp.log import setup_logging

from .io import read_initial_doctree

LF = TypeVar("LF", bound="LanguageFeature")
TRIPLE_QUOTE = re.compile("(\"\"\"|''')")
"""A regular expression matching the triple quotes used to delimit python docstrings."""

# fmt: off
# Order matters!
DEFAULT_MODULES = [
    "esbonio.lsp.directives",      # Generic directive support
    "esbonio.lsp.roles",           # Generic roles support
    "esbonio.lsp.rst.directives",  # Specialised support for docutils directives
    "esbonio.lsp.rst.roles",       # Specialised support for docutils roles
]
"""The modules to load in the default configuration of the server."""
# fmt: on


class CompletionContext:
    """Captures the context within which a completion request has been made."""

    def __init__(
        self,
        *,
        doc: Document,
        location: str,
        match: "re.Match",
        position: Position,
        capabilities: ClientCapabilities,
    ):

        self.doc: Document = doc
        """The document within which the completion request was made."""

        self.location: str = location
        """The location type where the request was made.
        See :meth:`~esbonio.lsp.rst.RstLanguageServer.get_location_type` for details."""

        self.match: "re.Match" = match
        """The match object describing the site of the completion request."""

        self.position: Position = position
        """The position at which the completion request was made."""

        self._client_capabilities: ClientCapabilities = capabilities

    def __repr__(self):
        p = f"{self.position.line}:{self.position.character}"
        return (
            f"CompletionContext<{self.doc.uri}:{p} ({self.location}) -- {self.match}>"
        )

    @property
    def commit_characters_support(self) -> bool:
        """Indicates if the client supports commit characters."""
        return self._client_capabilities.get_capability(
            "text_document.completion.completion_item.commit_characters_support", False
        )

    @property
    def deprecated_support(self) -> bool:
        """Indicates if the client supports the deprecated field on a
        ``CompletionItem``."""
        return self._client_capabilities.get_capability(
            "text_document.completion.completion_item.deprecated_support", False
        )

    @property
    def documentation_formats(self) -> List[MarkupKind]:
        """The list of documentation formats supported by the client."""
        return self._client_capabilities.get_capability(
            "text_document.completion.completion_item.documentation_format", []
        )

    @property
    def insert_replace_support(self) -> bool:
        """Indicates if the client supports ``InsertReplaceEdit``."""
        return self._client_capabilities.get_capability(
            "text_document.completion.completion_item.insert_replace_support", False
        )

    @property
    def preselect_support(self) -> bool:
        """Indicates if the client supports the preselect field on a
        ``CompletionItem``."""
        return self._client_capabilities.get_capability(
            "text_document.completion.completion_item.preselect_support", False
        )

    @property
    def snippet_support(self) -> bool:
        """Indicates if the client supports snippets"""
        return self._client_capabilities.get_capability(
            "text_document.completion.completion_item.snippet_support", False
        )

    @property
    def supported_tags(self) -> List[CompletionItemTag]:
        """The list of ``CompletionItemTags`` supported by the client."""
        capabilities = self._client_capabilities.get_capability(
            "text_document.completion.completion_item.tag_support", None
        )

        if not capabilities:
            return []

        return capabilities.value_set


class DocumentLinkContext:
    """Captures the context within which a document link request has been made."""

    def __init__(self, *, doc: Document, capabilities: ClientCapabilities):

        self.doc = doc
        """The document within which the document link request was made."""

        self._client_capabilities = capabilities

    @property
    def tooltip_support(self) -> bool:
        """Indicates if the client supports tooltips."""
        return self._client_capabilities.get_capability(
            "text_document.document_link.tooltip_support", False
        )


class DefinitionContext:
    """A class that captures the context within which a definition request has been
    made."""

    def __init__(
        self, *, doc: Document, location: str, match: "re.Match", position: Position
    ):

        self.doc = doc
        """The document within which the definition request was made."""

        self.location = location
        """The location type where the request was made.
        See :meth:`~esbonio.lsp.rst.RstLanguageServer.get_location_type` for details."""

        self.match = match
        """The match object describing the site of the definition request."""

        self.position = position
        """The position at which the definition request was made."""

    def __repr__(self):
        p = f"{self.position.line}:{self.position.character}"
        return (
            f"DefinitionContext<{self.doc.uri}:{p} ({self.location}) -- {self.match}>"
        )


class ImplementationContext:
    """A class that captures the context within which an implementation request has been
    made."""

    def __init__(
        self, *, doc: Document, location: str, match: "re.Match", position: Position
    ):

        self.doc = doc
        """The document within which the implementation request was made."""

        self.location = location
        """The location type where the request was made.
        See :meth:`~esbonio.lsp.rst.RstLanguageServer.get_location_type` for details."""

        self.match = match
        """The match object describing the site of the implementation request."""

        self.position = position
        """The position at which the implementation request was made."""

    def __repr__(self):
        p = f"{self.position.line}:{self.position.character}"
        return f"ImplementationContext<{self.doc.uri}:{p} ({self.location}) -- {self.match}>"


class HoverContext:
    """A class that captures the context within a hover request has been made."""

    def __init__(
        self,
        *,
        doc: Document,
        location: str,
        match: "re.Match",
        position: Position,
        capabilities: ClientCapabilities,
    ):

        self.doc = doc
        self.location = location
        self.match = match
        self.position = position
        self._client_capabilities = capabilities

    def __repr__(self):
        p = f"{self.position.line}:{self.position.character}"
        return f"HoverContext<{self.doc.uri}:{p} ({self.location}) -- {self.match}>"

    @property
    def content_formats(self) -> List[MarkupKind]:
        """The list of content formats supported by the client."""
        return self._client_capabilities.get_capability(
            "text_document.hover.content_format", []
        )


class LanguageFeature:
    """Base class for language features."""

    def __init__(self, rst: "RstLanguageServer"):
        self.rst = rst
        self.logger = rst.logger.getChild(self.__class__.__name__)

    def initialize(self, options: InitializeParams) -> None:
        """Called once when the server is first initialized."""

    def initialized(self, params: InitializedParams) -> None:
        """Called once upon receipt of the `initialized` notification from the client."""

    def on_shutdown(self, *args):
        """Called as the server is shutting down."""

    def save(self, params: DidSaveTextDocumentParams) -> None:
        """Called each time a document is saved."""

    def delete_files(self, params: DeleteFilesParams) -> None:
        """Called each time files are deleted."""

    def code_action(self, params: CodeActionParams) -> List[CodeAction]:
        """Called when code actions should be computed."""
        return []

    hover_triggers: List["re.Pattern"] = []

    def hover(self, context: HoverContext) -> str:
        """Called when request textDocument/hover is sent.

        This method shall return the contents value of textDocument/hover response.

        """
        return ""

    completion_triggers: List["re.Pattern"] = []
    """A list of regular expressions used to determine if the
    :meth`~esbonio.lsp.rst.LanguageFeature.complete` method should be called on the
    current line."""

    def complete(self, context: CompletionContext) -> List[CompletionItem]:
        """Called if any of the given ``completion_triggers`` match the current line.

        This method should return a list of ``CompletionItem`` objects.

        Parameters
        ----------
        context:
           The context of the completion request
        """
        return []

    def completion_resolve(self, item: CompletionItem) -> CompletionItem:
        """Called with a completion item the user has selected in the UI,
        allowing for additional details to be provided e.g. documentation.

        Parameters
        ----------
        item:
            The completion item to provide additional details for.
        """
        return item

    definition_triggers: List["re.Pattern"] = []
    """A list of regular expressions used to determine if the
    :meth:`~esbonio.lsp.rst.LanguageFeature.definition` method should be called."""

    def definition(self, context: DefinitionContext) -> List[Location]:
        """Called if any of the given ``definition_triggers`` match the current line.

        This method should return a list of ``Location`` objects.

        Parameters
        ----------
        context:
           The context of the definition request.
        """
        return []

    implementation_triggers: List["re.Pattern"] = []
    """A list of regular expressions used to determine if the
    :meth:`~esbonio.lsp.rst.LanguageFeature.implementation` method should be called."""

    def implementation(self, context: ImplementationContext) -> List[Location]:
        """Called if any of the given ``implementation_triggers`` match the current line.

        This method should return a list of ``Location`` objects.

        Parameters
        ----------
        context:
           The context of the implementation request.
        """
        return []

    def document_link(self, context: DocumentLinkContext) -> List[DocumentLink]:
        """Called whenever a ``textDocument/documentLink`` request is received."""
        return []


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

    log_level: str = Field("error", alias="logLevel")
    """The logging level of server messages to display."""

    log_filter: List[str] = Field(default_factory=list, alias="logFilter")
    """A list of logger names to restrict output to."""

    show_deprecation_warnings = Field(False, alias="showDeprecationWarnings")
    """Developer flag to enable deprecation warnings."""

    enable_scroll_sync: bool = Field(False, alias="enableScrollSync")
    """Enable custom transformation to add classes with line numbers"""

    enable_live_preview: bool = Field(False, alias="enableLivePreview")
    """Set it to True if you want to build Sphinx app on change event"""


class InitializationOptions(BaseModel):
    """The initialization options we can expect to receive from a client."""

    server: ServerConfig = Field(default_factory=ServerConfig)
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

        self._loaded_extensions: Dict[str, Any] = {}
        """Record of modules that have been loaded."""

        self._features: Dict[str, LanguageFeature] = {}
        """The collection of language features registered with the server."""

    @property
    def configuration(self) -> Dict[str, Any]:
        """Return the server's actual configuration."""
        if not self.user_config:
            return {}

        return self.user_config.dict()

    def initialize(self, params: InitializeParams):
        self.user_config = InitializationOptions(
            **typing.cast(Dict, params.initialization_options)
        )
        setup_logging(self, self.user_config.server)

    def initialized(self, params: InitializedParams):
        pass

    def on_shutdown(self, *args):
        pass

    def save(self, params: DidSaveTextDocumentParams):
        pass

    def delete_files(self, params: DeleteFilesParams):
        pass

    def build(self, force_all: bool = False, filenames: Optional[List[str]] = None):
        pass

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
            self.logger.error(
                "Unable to load extension '%s'\n%s", name, traceback.format_exc()
            )

    def add_feature(self, feature: "LanguageFeature"):
        """Register a language feature with the server.

        Parameters
        ----------
        feature
           The language feature
        """

        key = f"{feature.__module__}.{feature.__class__.__name__}"
        self._features[key] = feature

    @typing.overload
    def get_feature(self, key: str) -> "Optional[LanguageFeature]":
        ...

    @typing.overload
    def get_feature(self, key: Type[LF]) -> Optional[LF]:
        ...

    def get_feature(self, key):
        """Returns the requested language feature if it exists, otherwise it returns
        ``None``.

        Parameters
        ----------
        key: str | Type[LanguageFeature]
           A feature can be referenced either by its class definition (preferred) or by
           a string representing the language feature's dotted name e.g.
           ``a.b.c.ClassName``.

           .. deprecated:: 0.14.0

              Passing a string ``key`` to this method is deprecated and will become an
              error in ``v1.0``.
        """

        if isinstance(key, str):
            warnings.warn(
                "Language features should be referenced by their class definition, "
                "this will become an error in v1.0.",
                DeprecationWarning,
                stacklevel=2,
            )

        elif issubclass(key, LanguageFeature):
            key = f"{key.__module__}.{key.__name__}"

        else:
            raise TypeError("Expected language feature definition")

        return self._features.get(key, None)

    def get_doctree(
        self, *, docname: Optional[str] = None, uri: Optional[str] = None
    ) -> Optional[Any]:
        # Not currently implemented for vanilla docutils projects.
        return None

    def get_initial_doctree(self, uri: str) -> Optional[Any]:
        """Return the initial doctree corresponding to the specified document.

        An "initial" doctree can be thought of as the abstract syntax tree of a
        reStructuredText document. This method disables all role and directives
        from being executed, instead they are replaced with nodes that simply
        represent that they exist.

        Parameters
        ----------
        uri
           Returns the doctree that corresponds with the given uri.
        """

        doc = self.workspace.get_document(uri)
        loctype = self.get_location_type(doc, Position(line=1, character=0))

        if loctype != "rst":
            return None

        self.logger.debug("Getting initial doctree for: '%s'", Uri.to_fs_path(uri))

        try:
            return read_initial_doctree(doc, self.logger)
        except Exception:
            self.logger.error(traceback.format_exc())
            return None

    def get_directives(self) -> Dict[str, Directive]:
        """Return a dictionary of the known directives

        .. deprecated:: 0.14.2

           This will be removed in ``v1.0``.
           Use the :meth:`~esbonio.lsp.directives.Directives.get_directives` method
           instead.
        """

        clsname = self.__class__.__name__
        warnings.warn(
            f"{clsname}.get_directives() is deprecated and will be removed in v1.0."
            " Instead call the get_directives() method on the Directives language "
            "feature.",
            DeprecationWarning,
            stacklevel=2,
        )

        feature = self.get_feature("esbonio.lsp.directives.Directives")
        if feature is None:
            return {}

        return feature.get_directives()  # type: ignore

    def get_directive_options(self, name: str) -> Dict[str, Any]:
        """Return the options specification for the given directive.

        .. deprecated:: 0.14.2

           This will be removed in ``v1.0``
        """

        clsname = self.__class__.__name__
        warnings.warn(
            f"{clsname}.get_directive_options() is deprecated and will be removed in "
            "v1.0.",
            DeprecationWarning,
            stacklevel=2,
        )

        directive = self.get_directives().get(name, None)
        if directive is None:
            return {}

        return directive.option_spec or {}

    def get_roles(self) -> Dict[str, Any]:
        """Return a dictionary of known roles.

        .. deprecated:: 0.15.0

           This will be removed in ``v1.0``.
           Use the :meth:`~esbonio.lsp.roles.Roles.get_roles` method instead.
        """
        clsname = self.__class__.__name__
        warnings.warn(
            f"{clsname}.get_roles() is deprecated and will be removed in v1.0. "
            "Instead call the get_roles() method on the Roles language "
            "feature.",
            DeprecationWarning,
            stacklevel=2,
        )

        feature = self.get_feature("esbonio.lsp.roles.Roles")
        if feature is None:
            return {}

        return feature.get_roles()  # type: ignore

    def get_default_role(self) -> Tuple[Optional[str], Optional[str]]:
        """Return the default role for the project."""
        return None, None

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

        if uri:
            uri = normalise_uri(uri)

        for key in self._diagnostics.keys():
            clear_source = source == key[0]
            clear_uri = uri == key[1] or uri is None

            if clear_source and clear_uri:
                self._diagnostics[key] = []

    def add_diagnostics(self, source: str, uri, diagnostic: Diagnostic):
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
        key = (source, normalise_uri(uri))
        self._diagnostics.setdefault(key, []).append(diagnostic)

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

        for uri, diag_list in diagnostics.items():
            self.logger.debug("Publishing %d diagnostics for: %s", len(diag_list), uri)
            self.publish_diagnostics(uri, diag_list.data)

    def get_location_type(self, document: Document, position: Position) -> str:
        """Given a document and a position, return the type of location.

        Returns one of the following values:

        - ``rst``: Indicates that the position is within an reStructuredText document
        - ``py``: Indicates that the position is within code in a Python file
        - ``docstring``: Indicates that the position is within a docstring in a
          Python file.

        If the location type cannot be determined, this function will fall back to
        ``rst``.

        Parameters
        ----------
        doc
           The document associated with the given position

        position
           The position to determine the type of
        """
        doc = self.workspace.get_document(document.uri)
        fpath = pathlib.Path(Uri.to_fs_path(doc.uri))

        # Prefer the document's language_id, but fallback to file extensions
        loctype = getattr(doc, "language_id", None) or fpath.suffix

        if loctype in {".rst", "rst", "restructuredtext"}:
            return "rst"

        if loctype in {".py", "py", "python"}:

            # Let's count how many pairs of triple quotes are above us in the file
            # even => we're outside a docstring
            # odd  => we're within a docstring
            source = self.text_to_position(doc, position)
            count = len(TRIPLE_QUOTE.findall(source))
            return "py" if count % 2 == 0 else "docstring"

        # Fallback to rst
        self.logger.debug("Unable to determine location type for uri: %s", doc.uri)
        return "rst"

    def line_at_position(self, doc: Document, position: Position) -> str:
        """Return the contents of the line corresponding to the given position.

        Parameters
        ----------
        doc:
           The document associated with the given position
        position:
           The position representing the line to retrieve
        """

        try:
            return doc.lines[position.line]
        except IndexError:
            return ""

    def line_to_position(self, doc: Document, position: Position) -> str:
        """Return the contents of the line up until the given position.

        Parameters
        ----------
        doc:
           The document associated with the given position.
        position:
           The position representing the line to retrieve.
        """

        line = self.line_at_position(doc, position)
        return line[: position.character]

    def preview(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a preview of the documentation."""
        name = self.__class__.__name__
        self.show_message(
            f"Previews are not currently supported by {name} based servers"
        )

        return {}

    def text_to_position(self, doc: Document, position: Position) -> str:
        """Return the contents of the document up until the given position.

        Parameters
        ----------
        doc:
           The document associated with the given position
        position:
           The position representing the point at which to stop gathering text.
        """
        idx = doc.offset_at_position(position)
        return doc.source[:idx]


def normalise_uri(uri: str) -> str:

    uri = Uri.from_fs_path(Uri.to_fs_path(uri))

    # Paths on windows are case insensitive.
    if IS_WIN:
        uri = uri.lower()

    return uri


def _get_setup_arguments(
    server: RstLanguageServer, setup: Callable, modname: str
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


cli = setup_cli("esbonio.lsp.rst", "Esbonio's reStructuredText language server.")
cli.set_defaults(modules=DEFAULT_MODULES)
cli.set_defaults(server_cls=RstLanguageServer)
