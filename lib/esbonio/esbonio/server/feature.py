from __future__ import annotations

import typing
from typing import List
from typing import Optional

from lsprotocol import types

if typing.TYPE_CHECKING:
    from .server import EsbonioLanguageServer


class LanguageFeature:
    """Base class for language features."""

    def __init__(self, server: EsbonioLanguageServer):
        self.server = server
        self.converter = server.converter
        self.logger = server.logger.getChild(self.__class__.__name__)

    def document_change(self, params: types.DidChangeTextDocumentParams):
        """Called when a text document is changed."""

    def document_close(self, params: types.DidCloseTextDocumentParams):
        """Called when a text document is closed."""

    def document_open(self, params: types.DidOpenTextDocumentParams):
        """Called when a text document is opened."""

    def document_save(self, params: types.DidSaveTextDocumentParams):
        """Called when a text document is saved."""

    def document_symbol(
        self, params: types.DocumentSymbolParams
    ) -> Optional[List[types.DocumentSymbol]]:
        """Called when a document symbols request it received."""
        ...
