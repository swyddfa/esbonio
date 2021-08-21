import re
import typing
from typing import List

from pygls.lsp.types import CompletionItem
from pygls.lsp.types import DidSaveTextDocumentParams
from pygls.lsp.types import InitializedParams
from pygls.lsp.types import InitializeParams
from pygls.lsp.types import Location
from pygls.lsp.types import Position
from pygls.workspace import Document

if typing.TYPE_CHECKING:
    from .rst import RstLanguageServer


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
    :meth`~esbonio.lsp.feature.LanguageFeature.complete` method should be called on the
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
    :meth:`~esbonio.lsp.feature.LanguageFeature.definition` method should be called."""

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
