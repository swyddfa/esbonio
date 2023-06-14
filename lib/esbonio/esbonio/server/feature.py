from __future__ import annotations

import typing

from lsprotocol.types import DidChangeTextDocumentParams
from lsprotocol.types import DidCloseTextDocumentParams
from lsprotocol.types import DidOpenTextDocumentParams
from lsprotocol.types import DidSaveTextDocumentParams

if typing.TYPE_CHECKING:
    from .server import EsbonioLanguageServer


class LanguageFeature:
    """Base class for language features."""

    def __init__(self, server: EsbonioLanguageServer):
        self.server = server
        self.converter = server.converter
        self.logger = server.logger.getChild(self.__class__.__name__)

    def document_change(self, params: DidChangeTextDocumentParams):
        """Called when a text document is changed."""

    def document_close(self, params: DidCloseTextDocumentParams):
        """Called when a text document is closed."""

    def document_open(self, params: DidOpenTextDocumentParams):
        """Called when a text document is opened."""

    def document_save(self, params: DidSaveTextDocumentParams):
        """Called when a text document is saved."""
