import collections
import importlib
import logging
import pathlib
import re
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

import pygls.uris as Uri
from docutils.nodes import NodeVisitor
from docutils.parsers.rst import Directive
from docutils.parsers.rst import directives
from docutils.parsers.rst import nodes
from docutils.parsers.rst import roles
from pydantic import BaseModel
from pydantic import Field
from pygls import IS_WIN
from pygls.lsp.types import CompletionItem
from pygls.lsp.types import Diagnostic
from pygls.lsp.types import DidSaveTextDocumentParams
from pygls.lsp.types import DocumentSymbol
from pygls.lsp.types import InitializedParams
from pygls.lsp.types import InitializeParams
from pygls.lsp.types import Location
from pygls.lsp.types import Position
from pygls.lsp.types import Range
from pygls.lsp.types import SymbolKind
from pygls.server import LanguageServer
from pygls.workspace import Document

from .log import LOG_LEVELS
from .log import LogFilter
from .log import LspHandler

TRIPLE_QUOTE = re.compile("(\"\"\"|''')")
"""A regular expression matching the triple quotes used to delimit python docstrings."""


class CompletionContext:
    """A class that captures the context within which a completion request has been
    made."""

    def __init__(
        self, *, doc: Document, location: str, match: "re.Match", position: Position
    ):

        self.doc = doc
        """The document within which the completion request was made."""

        self.location = location
        """The location type where the request was made.
        See :meth:`~esbonio.lsp.rst.RstLanguageServer.get_location_type` for details."""

        self.match = match
        """The match object describing the site of the completion request."""

        self.position = position
        """The position at which the completion request was made."""

    def __repr__(self):
        p = f"{self.position.line}:{self.position.character}"
        return (
            f"CompletionContext<{self.doc.uri}:{p} ({self.location}) -- {self.match}>"
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

    def save(self, params: DidSaveTextDocumentParams) -> None:
        """Called each time a document is saved."""

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

    definition_triggers: List["re.Pattern"] = []
    """A list of regular expressions used to determine if the
    :meth:`~esbonio.lsp.rst.LanguageFeature.definition` method should be called."""

    def definition(
        self, match: "re.Match", doc: Document, pos: Position
    ) -> List[Location]:
        """Called if any of the given ``definition_triggers`` match the current line.

        This method should return a list of ``Location`` objects.

        Parameters
        ----------
        match:
           The match object generated from the corresponding regular expression.
        doc:
           The document the definition has been requested within
        pos:
           The position of the request within the document.
        """
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

    def get_doctree(
        self, *, docname: Optional[str] = None, uri: Optional[str] = None
    ) -> Optional[Any]:
        return None

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

    def get_default_role(self) -> Optional[Tuple[Optional[str], str]]:
        """Return the default role for the project."""
        return None

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

    def get_location_type(self, doc: Document, position: Position) -> str:
        """Given a document and a position, return the kind of location that
        represents.

        This will return one of the following values:

        - ``rst``: Indicates that the position is within an ``*.rst`` document
        - ``py``: Indicates that the position is within code in a ``*.py`` document
        - ``docstring``: Indicates that the position is within a docstring in a
          ``*.py`` document.

        Parameters
        ----------
        doc:
           The document associated with the given position
        position:
           The position to determine the type of.
        """
        ext = pathlib.Path(Uri.to_fs_path(doc.uri)).suffix

        if ext == ".rst":
            return "rst"

        if ext == ".py":

            # Let's count how many pairs of triple quotes are "above" us in the file
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


class SymbolVisitor(NodeVisitor):
    """A visitor used to build the hierarchy we return from a
    ``textDocument/documentSymbol`` request.

    Currently this only looks at sections.
    """

    def __init__(self, rst, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.logger = rst.logger
        self.symbols = []
        self.symbol_stack = []

    @property
    def current_symbol(self) -> DocumentSymbol:

        if len(self.symbol_stack) == 0:
            return None

        return self.symbol_stack[-1]

    def push_symbol(self):
        symbol = DocumentSymbol(
            name="",
            kind=SymbolKind.String,
            range=Range(
                start=Position(line=1, character=0),
                end=Position(line=1, character=10),
            ),
            selection_range=Range(
                start=Position(line=1, character=0),
                end=Position(line=1, character=10),
            ),
            children=[],
        )
        current_symbol = self.current_symbol

        if not current_symbol:
            self.symbols.append(symbol)
        else:
            current_symbol.children.append(symbol)

        self.symbol_stack.append(symbol)

    def pop_symbol(self):
        self.symbol_stack.pop()

    def visit_section(self, node: nodes.Node) -> None:
        self.push_symbol()

    def depart_section(self, node: nodes.Node) -> None:
        self.pop_symbol()

    def visit_title(self, node: nodes.Node) -> None:

        symbol = self.current_symbol
        name = node.astext()
        line = node.line - 1

        symbol.name = name
        symbol.range.start.line = line
        symbol.range.end.line = line
        symbol.range.end.character = len(name) - 1
        symbol.selection_range.start.line = line
        symbol.selection_range.end.line = line
        symbol.selection_range.end.character = len(name) - 1

    def depart_title(self, node: nodes.Node) -> None:
        pass

    def visit_Text(self, node: nodes.Node) -> None:
        pass

    def depart_Text(self, node: nodes.Node) -> None:
        pass

    def unknown_visit(self, node: nodes.Node) -> None:
        pass

    def unknown_departure(self, node: nodes.Node) -> None:
        pass


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
