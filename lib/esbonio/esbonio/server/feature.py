from __future__ import annotations

import typing
from typing import Literal

import attrs
from lsprotocol import types
from pygls.capabilities import get_capability
from pygls.workspace import TextDocument

from . import Uri

if typing.TYPE_CHECKING:
    import re
    from typing import Any
    from typing import Coroutine
    from typing import List
    from typing import Optional
    from typing import Set
    from typing import Union

    from .server import EsbonioLanguageServer

    CompletionResult = Union[
        Optional[List[types.CompletionItem]],
        Coroutine[Any, Any, Optional[List[types.CompletionItem]]],
    ]

    DocumentSymbolResult = Union[
        Optional[List[types.DocumentSymbol]],
        Coroutine[Any, Any, Optional[List[types.DocumentSymbol]]],
    ]

    MaybeAsyncNone = Union[
        None,
        Coroutine[Any, Any, None],
    ]

    WorkspaceSymbolResult = Union[
        Optional[List[types.WorkspaceSymbol]],
        Coroutine[Any, Any, Optional[List[types.WorkspaceSymbol]]],
    ]


class LanguageFeature:
    """Base class for language features."""

    def __init__(self, server: EsbonioLanguageServer):
        self.server = server
        self.logger = server.logger.getChild(self.__class__.__name__)

    @property
    def converter(self):
        return self.server.converter

    @property
    def configuration(self):
        return self.server.configuration

    def initialize(self, params: types.InitializeParams) -> MaybeAsyncNone:
        """Called during ``initialize``."""

    def initialized(self, params: types.InitializedParams) -> MaybeAsyncNone:
        """Called when the ``initialized`` notification is received."""

    def shutdown(self, params: None) -> MaybeAsyncNone:
        """Called when the server is instructed to ``shutdown`` by the client."""

    def document_change(
        self, params: types.DidChangeTextDocumentParams
    ) -> MaybeAsyncNone:
        """Called when a text document is changed."""

    def document_close(
        self, params: types.DidCloseTextDocumentParams
    ) -> MaybeAsyncNone:
        """Called when a text document is closed."""

    def document_open(self, params: types.DidOpenTextDocumentParams) -> MaybeAsyncNone:
        """Called when a text document is opened."""

    def document_save(self, params: types.DidSaveTextDocumentParams) -> MaybeAsyncNone:
        """Called when a text document is saved."""

    completion_trigger: Optional[CompletionTrigger] = None

    def completion(self, context: CompletionContext) -> CompletionResult:
        """Called when a completion request matches one of the specified triggers."""

    def document_symbol(
        self, params: types.DocumentSymbolParams
    ) -> DocumentSymbolResult:
        """Called when a document symbols request is received."""

    def workspace_symbol(
        self, params: types.WorkspaceSymbolParams
    ) -> WorkspaceSymbolResult:
        """Called when a workspace symbols request is received."""


@attrs.define
class CompletionTrigger:
    """Define when the feature's completion method should be called."""

    patterns: List[re.Pattern]
    """A list of regular expressions to try"""

    languages: Set[str] = attrs.field(factory=set)
    """Languages in which the completion trigger should fire.

    If empty, the document's language will be ignored.
    """

    characters: Set[str] = attrs.field(factory=set)
    """Characters which, when typed, should trigger a completion request.

    If empty, this trigger will ignore any trigger characters.
    """

    def __call__(
        self,
        uri: Uri,
        params: types.CompletionParams,
        document: TextDocument,
        language: str,
        client_capabilities: types.ClientCapabilities,
    ) -> Optional[CompletionContext]:
        """Determine if this completion trigger should fire.

        Parameters
        ----------
        uri
           The uri of the document in which the completion request was made

        params
           The completion params sent from the client

        document
           The document in which the completion request was made

        language
           The language at the point where the completion request was made

        client_capabilities
           The client's capabilities

        Returns
        -------
        Optional[CompletionContext]
           A completion context, if this trigger has fired
        """

        if len(self.languages) > 0 and language not in self.languages:
            return None

        if not self._trigger_characters_match(params):
            return None

        try:
            line = document.lines[params.position.line]
        except IndexError:
            line = ""

        for pattern in self.patterns:
            for match in pattern.finditer(line):
                # Only trigger completions if the position of the request is within the
                # match.
                start, stop = match.span()
                if not (start <= params.position.character <= stop):
                    continue

                return CompletionContext(
                    uri=uri,
                    doc=document,
                    match=match,
                    position=params.position,
                    language=language,
                    capabilities=client_capabilities,
                )

        return None

    def _trigger_characters_match(self, params: types.CompletionParams) -> bool:
        """Determine if this trigger's completion characters align with the request."""

        if (context := params.context) is None:
            # No context available, assume a match
            return True

        if context.trigger_kind != types.CompletionTriggerKind.TriggerCharacter:
            # Not a trigger character request, assume a match
            return True

        if (char := context.trigger_character) is None or len(self.characters) == 0:
            return True

        return char in self.characters


@attrs.define
class CompletionConfig:
    """Configuration options that control completion behavior."""

    preferred_insert_behavior: Literal["insert", "replace"] = attrs.field(
        default="replace"
    )
    """This option indicates if the user prefers we use ``insertText`` or ``textEdit``
    when rendering ``CompletionItems``."""


@attrs.define
class CompletionContext:
    """Captures the context within which a completion request has been made."""

    uri: Uri
    """The uri for the document in which the completion request was made."""

    doc: TextDocument
    """The document within which the completion request was made."""

    match: re.Match
    """The match object describing the site of the completion request."""

    position: types.Position
    """The position at which the completion request was made."""

    language: str
    """The language where the completion request was made."""

    capabilities: types.ClientCapabilities
    """The client's capabilities."""

    def __repr__(self):
        p = f"{self.position.line}:{self.position.character}"
        return f"CompletionContext<{self.doc.uri}:{p} -- {self.match}>"

    @property
    def commit_characters_support(self) -> bool:
        """Indicates if the client supports commit characters."""
        return get_capability(
            self.capabilities,
            "text_document.completion.completion_item.commit_characters_support",
            False,
        )

    @property
    def deprecated_support(self) -> bool:
        """Indicates if the client supports the deprecated field on a
        ``CompletionItem``."""
        return get_capability(
            self.capabilities,
            "text_document.completion.completion_item.deprecated_support",
            False,
        )

    @property
    def documentation_formats(self) -> List[types.MarkupKind]:
        """The list of documentation formats supported by the client."""
        return get_capability(
            self.capabilities,
            "text_document.completion.completion_item.documentation_format",
            [],
        )

    @property
    def insert_replace_support(self) -> bool:
        """Indicates if the client supports ``InsertReplaceEdit``."""
        return get_capability(
            self.capabilities,
            "text_document.completion.completion_item.insert_replace_support",
            False,
        )

    @property
    def preselect_support(self) -> bool:
        """Indicates if the client supports the preselect field on a
        ``CompletionItem``."""
        return get_capability(
            self.capabilities,
            "text_document.completion.completion_item.preselect_support",
            False,
        )

    @property
    def snippet_support(self) -> bool:
        """Indicates if the client supports snippets"""
        return get_capability(
            self.capabilities,
            "text_document.completion.completion_item.snippet_support",
            False,
        )

    @property
    def supported_tags(self) -> List[types.CompletionItemTag]:
        """The list of ``CompletionItemTags`` supported by the client."""
        capabilities = get_capability(
            self.capabilities,
            "text_document.completion.completion_item.tag_support",
            None,
        )

        if not capabilities:
            return []

        return capabilities.value_set
