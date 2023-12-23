from __future__ import annotations

import typing
from typing import Any
from typing import Coroutine
from typing import List
from typing import Optional
from typing import Union

from lsprotocol import types

if typing.TYPE_CHECKING:
    from .server import EsbonioLanguageServer


DocumentSymbolResult = Union[
    Optional[List[types.DocumentSymbol]],
    Coroutine[Any, Any, Optional[List[types.DocumentSymbol]]],
]

WorkspaceSymbolResult = Union[
    Optional[List[types.WorkspaceSymbol]],
    Coroutine[Any, Any, Optional[List[types.WorkspaceSymbol]]],
]


class LanguageFeature:
    """Base class for language features."""

    def __init__(self, server: EsbonioLanguageServer):
        self.server = server
        self.converter = server.converter
        self.logger = server.logger.getChild(self.__class__.__name__)

    def initialize(self, params: types.InitializeParams):
        """Called during ``initialize``."""

    def initialized(self, params: types.InitializedParams):
        """Called when the ``initialized`` notification is received."""

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
    ) -> DocumentSymbolResult:
        """Called when a document symbols request is received."""
        ...

    def workspace_symbol(
        self, params: types.WorkspaceSymbolParams
    ) -> WorkspaceSymbolResult:
        """Called when a workspace symbols request is received."""
        ...
