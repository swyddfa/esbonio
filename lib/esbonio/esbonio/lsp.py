"""lsp - Language Server Protocol.

This module is the implementation of the language server provided by esbonio.

For the language server protocol specification please see:
https://microsoft.github.io/language-server-protocol/specifications/specification-current/

While large, the bulk of this module is simply defining the classes used to represent
the data that is communicated between the client and server.

For low level details on how requests/responses are handled see the ``LanguageServer``
class.

For the actual implementation of the Rst lanaguage server see the ``RstLanguageServer``
class.
"""
from __future__ import annotations

import enum
import inspect
import json
import logging
import sys
import typing

from dataclasses import asdict, dataclass, field, fields, is_dataclass
from typing import Any, Dict, List, Optional, Union, Tuple

from esbonio import __version__ as VERSION

class LanguageServer:
    """Base class that handles all the low level details of language server protocol.

    Actual implementations should subclass this and provide methods of the form::

        def methodname(self, params: ParamsType):
            ...

    where:

    - ``methodname`` corresponds with a method name from the protocol they wish to
      handle.
    - ``ParamsType`` is a dataclass that models the parameters that method can receive.
    - On success the method should return the result object it wishes to send back to
      the client.
    - On failure the method should raise the appropriate error it wishes to communicate
      back to the client.
    """

    def __init__(self):
        self.running = False
        # For logging request/responses.
        self.reqlog = logging.getLogger(__name__ + ".requests")
        self.reslog = logging.getLogger(__name__ + ".responses")

    def _dispatch(self, message: RequestMessage) -> ResponseMessage:
        """Given a message, find an appropriate handler and call it."""

        handler = getattr(self, message.method, None)
        if handler is None or not callable(handler):
            raise NotImplementedError(f"Unable to handle message '{message.method}'")

        parameters = inspect.signature(handler).parameters
        if "params" not in parameters:
            raise TypeError(f"Handler {handler} does not accept 'params' argument.")

        hints = typing.get_type_hints(handler)
        params_type = hints.get("params", None)
        if params_type is None:
            raise TypeError(f"Missing type annotation for 'params' in {handler}")

        params = parse_as(message.params, params_type)
        result = handler(params)

        return ResponseMessage.from_result(message.id, result)

    def run(self):
        """Start the server."""
        self.running = True
        length = 0

        # TODO: Add sanity checking, error handling etc.
        # TODO: Refactor this to use async / await?
        while self.running:
            # Keep reading lines until we find the "Content-Length" header.
            # TODO: Abstract out where we read the messages from.
            line = sys.stdin.readline()
            if line.startswith("Content-Length"):
                length = int(line.split(":")[1].strip())

            # Once we reach the end of the header, parse the actual message
            # and handle it.
            if line == "\r\n":
                chars = sys.stdin.read(length)
                self.reqlog.debug("Content-Length: %s\n%s", length, chars)
                msg = parse_as(json.loads(chars), RequestMessage)

                resp = self._dispatch(msg)
                self._write_response(resp)

    def _write_response(self, resp):
        msg = {k: v for k, v in asdict(resp).items() if v is not None}
        chars = json.dumps(msg)
        msg_length = len(chars)

        header = f"Content-Length: {msg_length}"
        self.reslog.debug("%s\n%s", header, chars)

        # TODO: Abstract out where we write our messages to.
        sys.stdout.write(f"{header}\r\n\r\n{chars}")


class RstLanguageServer(LanguageServer):
    """The actual RST language server implementation."""

    def initialize(self, params: InitializeParams) -> InitializeResult:
        capabilities = ServerCapabilities()
        info = ServerInfo('esbonio', VERSION)
        return InitializeResult(capabilities=capabilities, serverInfo=info)

#                              Helpers and Utilities
#
# Below this comment lies any helper functions used by this module.

def parse_as(message, cls):
    """Given a message and the class representing it, construct an instance from the
    message."""

    message = dict(message)

    for field in fields(cls):
        field_name = field.name

        # Recusively initialise any fields represented by another data class.
        if is_dataclass(field.type) and field_name in message:
            message[field_name] = parse_as(message[field_name], field)

    return cls(**message)

#                               Data Model
#
# Below this comment lies the data model used by the Language Server Protocol.
# You should find very little / no logic from here on it, just a *long* list of class
# definitions.

#                               Params & Results
#
# This section of the data model defines the "XXXParams" and "XXXResult" objects that
# correspond with a given Request/Response pair in the protocol.
@dataclass
class InitializeParams:
    """Represents the parameters the client can send as part of the "initialize"
    request"""

    processId: Optional[int]
    """The process ID of the process that started the server."""

    rootUri: DocumentUri
    """The rootUri of the workspace, if null then no folder is open."""

    capabilities: ClientCapabilities
    """The capabilities provided by the client."""

    clientInfo: Optional[ClientInfo] = field(default=None)
    """Information about the client."""

    rootPath: Optional[str] = field(default=None)
    """The rootPath of the workspace. Deprecated in favour of rootUri"""

    initializationOptions: Optional[Any] = field(default=None)
    """User provided initialization options."""

    trace: Optional[str] = field(default=None)
    """The initial trace setting."""

    workspaceFolders: Optional[List[WorkspaceFolder]] = field(default=None)
    """Workspace folders configured in the client."""

@dataclass
class InitializeResult:
    """The response the server should send after an "initialize" request."""

    capabilities: ServerCapabilities
    """The object that describes what the server is capable of providing."""

    serverInfo: Optional[ServerInfo] = field(default=None)
    """Optional information describing the server."""


#                               JSON RPC
#
# This section defines the objects used to model the JSON RPC layer of the protocol
# which typically wraps the objects defined above in some way.

@dataclass
class RequestMessage:
    """Represents the Request a client sends to the server."""

    jsonrpc: str
    """The version string of the rpc message."""

    id: int
    """The id of the request."""

    method: str
    """The method the message is calling."""

    params: Union[Dict[str, Any], List[Dict[str, Any]]]
    """The parameters sent to the method."""


@dataclass
class ResponseError:
    """Represents an error."""

    code: int
    """Error code indicating the type of error."""

    message: str
    """The error message"""

    data: Optional[Any] = field(default=None)
    """Additional detail describing the error."""


class LspException(Exception):
    """Base exception type for errors featured in the language server protocol."""

    def __init__(self, code: int, message: str, data: Optional[Any] = None):

        self.code = code
        """Error code indicating the type of error."""

        self.message = message
        """The error message"""

        self.data = data
        """Additional detail describing the error."""

    def to_error(self) -> ResponseError:
        """Convert into a ResponseError."""
        return ResponseError(self.code, self.message, self.data)


class LspParseError(LspException):
    def __init__(self, message: str, data: Optional[Any] = None):
        super().__init__(-32700, message, data)


class LspInvalidRequestError(LspException):
    def __init__(self, message: str, data: Optional[Any] = None):
        super().__init__(-32600, message, data)


class LspMethodNotFound(LspException):
    def __init__(self, message: str, data: Optional[Any] = None):
        super().__init__(-32601, message, data)


class LspInvalidParams(LspException):
    def __init__(self, message: str, data: Optional[Any] = None):
        super().__init__(-32602, message, data)


class LspInternalError(LspException):
    def __init__(self, message: str, data: Optional[Any] = None):
        super().__init__(-32603, message, data)


class LspServerErrorStart(LspException):
    def __init__(self, message: str, data: Optional[Any] = None):
        super().__init__(-32099, message, data)


class LspServerErrorEnd(LspException):
    def __init__(self, message: str, data: Optional[Any] = None):
        super().__init__(-32000, message, data)


class LspServerNotInitialised(LspException):
    def __init__(self, message: str, data: Optional[Any] = None):
        super().__init__(-32002, message, data)


class LspUnknownError(LspException):
    def __init__(self, message: str, data: Optional[Any] = None):
        super().__init__(-32001, message, data)


class LspRequestCancelled(LspException):
    def __init__(self, message: str, data: Optional[Any] = None):
        super().__init__(-32800, message, data)


class LspContentModified(LspException):
    def __init__(self, message: str, data: Optional[Any] = None):
        super().__init__(-32801, message, data)


@dataclass
class ResponseMessage:
    """Represents the Response the server sends to the client."""

    jsonrpc: str
    """The version string of the rpc message"""

    id: int
    """The id of the request the message is in response to."""

    result: Optional[Any] = field(default=None)
    """The result of the request. This field cannot be in the response we send if
    there's an error."""

    error: Optional[ResponseError] = field(default=None)

    @classmethod
    def from_result(cls, id_, result):
        """Construct a response from a successful result."""
        return cls("2.0", id_, result=result)

    @classmethod
    def from_error(cls, id_, error: ResponseError):
        """Construct a response from an error."""
        return cls("2.0", id_, error=error)

#                                   Everything Else
#
# Here now lies the vast sea of object definitions that model everything that the
# protocol can describe.
#
# TODO: Once the protocol is better understood, sort this list into a more logical order

DocumentUri = str

@dataclass
class ClientInfo:
    """Information about the client."""

    name: str
    """The name of the client."""

    version: Optional[str] = field(default=None)
    """The version of the client."""

@dataclass
class ServerInfo:
    """Information about the server."""

    name: str
    """The name of the server."""

    version: Optional[str] = field(default=None)
    """The version of the server."""


class CodeActionKind(enum.Enum):
    """The kinds of code actions."""

    EMPTY = ""
    """Empty kind"""

    QUICKFIX = "quickfix"
    """Base kind for quickfix actions"""

    REFACTOR = "refactor"
    """Base kind for refactoring actions"""

    REFACTOR_EXTRACT = "refactor.extract"
    """Base kind for refactor by extraction actions."""

    REFACTOR_INLINE = "refactor.inline"
    """Base kind for refactor inline actions."""

    REFACTOR_REWRITE = "refactor.rewrite"
    """Base kind for refactor rewrite actions."""

    SOURCE = "source"
    """Base kind for source actions"""

    SOURCE_ORGANISE_IMPORTS = "source.organizeImports"
    """Base kind for organise imports source action."""


class CompletionItemKind(enum.IntEnum):
    """The kind of completion item."""

    TEXT = 1
    METHOD = 2
    FUNCTION = 3
    CONSTRUCTOR = 4
    FIELD = 5
    VARIABLE = 6
    CLASS = 7
    INTERFACE = 8
    MODULE = 9
    PROPERTY = 10
    UNIT = 11
    VALUE = 12
    ENUM = 13
    KEYWORD = 14
    SNIPPET = 15
    COLOR = 16
    FILE = 17
    REFERENCE = 18
    FOLDER = 19
    ENUMMEMBER = 20
    CONSTANT = 21
    STRUCT = 22
    EVENT = 23
    OPERATOR = 24
    TYPEPARAMETER = 25


class CompletionItemTag(enum.IntEnum):
    """Completion item tags are annotations that can control the rendering of an item at
    completion time."""

    DEPRECATED = 1
    """Render a completion as obselete, usually with a strike-out"""

class DiagnosticSeverity(enum.IntEnum):
    """Indicates how severe a given diagnosis is."""

    ERROR = 1
    WARNING = 2
    INFORMATION = 3
    HINT = 4


class DiagnosticTag(enum.IntEnum):
    """Hints indicating how diagnostic tags should be rendered."""

    UNNECESSARY = 1
    """Unused code, client can render this as being faded out."""

    DEPRECATED = 2
    """Deprecated code, client can render this with a strikethrough."""


class FailureHandlingKind(enum.Enum):
    """How a client handles failures when trying to apply workspace changes."""

    ABORT = "abort"
    """Applying the workspace change is simply aborted if one of the changes fail.
    Any existing operations executed before the failure stay executed."""

    TRANSACTIONAL = "transactional"
    """Operations are transactional. Either all changes succeed or none are applied."""

    TEXT_ONLY_TRANSACTIONAL = "textOnlyTransactional"
    """If the edit contains only text file changes, they are executed as a transaction.
    If there are resource changes, the strategy is to abort."""

    UNDO = "undo"
    """Client will try to undo any operations already executed. But no guarantees are
    made in it succeeding."""


class MarkupKind(enum.Enum):
    """Markup kinds reprents the format that some content is formatted in."""

    MARKDOWN = "markdown"
    PLAIN_TEXT = "plaintext"


class ResourceOperationKind(enum.Enum):
    """Resource Operations supported by a client."""

    CREATE = "create"
    """Support for creating new files and folders."""

    RENAME = "rename"
    """Support for renaming existing files and folders."""

    DELETE = "delete"
    """Support for deleting exising files and folders."""


class SymbolKind(enum.IntEnum):
    """Kinds of symbol."""

    FILE = 1
    MODULE = 2
    NAMESPACE = 3
    PACKAGE = 4
    CLASS = 5
    METHOD = 6
    PROPERTY = 7
    FIELD = 8
    CONSTRUCTOR = 9
    ENUM = 10
    INTERFACE = 11
    FUNCTION = 12
    VARIABLE = 13
    CONSTANT = 14
    STRING = 15
    NUMBER = 16
    BOOLEAN = 17
    ARRAY = 18
    OBJECT = 19
    KEY = 20
    NULL = 21
    ENUMMEMBER = 22
    STRUCT = 23
    EVENT = 24
    OPERATOR = 25
    TYPEPARAMETER = 26


class TexrDocumentSyncKind(enum.IntEnum):
    NONE = 0
    """Documents should not be synced at all."""

    FULL = 1
    """Documents are synced by always sending the full document"""

    INCREMENTAL = 2
    """Documents are synced by sending the full content on open, with incremental
    updates from then on."""


@dataclass
class MarkupContent:
    kind: MarkupKind
    value: str


@dataclass
class CodeActionClientCapabilities:
    # fmt: off
    codeActionLiteralSuport: Optional[CodeActionLiteralCapabilities] = field(default=None)
    dynamicRegistration: Optional[bool] = field(default=None)
    isPreferredSupport: Optional[bool] = field(default=None)
    # fmt: on

@dataclass
class CodeActionKindCapabilities:
    valueSet: List[CodeActionKind] = field(default_factory=list)

@dataclass
class CodeActionLiteralCapabilities:
    # fmt: on
    codeActionKind: CodeActionKindCapabilities = field(default=None)
    # fmt: off

@dataclass
class CodeActionOptions:
    codeActionKinds: Optional[List[CodeActionKind]] = field(default=None)

@dataclass
class CodeLensClientCapabilities:
    dynamicRegistration: Optional[bool] = field(default=None)

@dataclass
class CompletionClientCapabilities:
    dynamicRegistration: Optional[bool] = field(default=None)
    completionItem: Optional[CompletionItemCapabilities] = field(default=None)
    completionItemKind: Optional[List[CompletionItemKind]] = field(default_factory=list)
    contextSupport: Optional[bool] = field(default=None)

@dataclass
class CompletionOptions:
    allCommitCharacters: Optional[List[str]] = field(default=None)
    resolveProvider: Optional[bool] = field(default=None)
    triggerCharacters: Optional[List[str]] = field(default=None)

@dataclass
class CompletionItemCapabilities:
    commitCharactersSupport: Optional[bool] = field(default=None)
    deprecatedSupport: Optional[bool] = field(default=None)
    documentationFormat: Optional[List[MarkupKind]] = field(default_factory=list)
    preselectSupport: Optional[bool] = field(default=None)
    snippetSupport: Optional[bool] = field(default=None)
    tagSupport: Optional[CompletionItemTagCapabilities] = field(default=None)


@dataclass
class CompletionItemTagCapabilities:
    valueSet: Optional[List[CompletionItemTag]] = field(default_factory=list)


@dataclass
class DeclarationClientCapabilities:
    dynamicRegistration: Optional[bool] = field(default=None)
    linkSupport: Optional[bool] = field(default=None)

@dataclass
class DefinitionClientCapabilities:
    dynamicRegistration: Optional[bool] = field(default=None)
    linkSupport: Optional[bool] = field(default=None)

@dataclass
class DocumentColorClientCapabilities:
    dynamicRegistration: Optional[bool] = field(default=None)

@dataclass
class DocumentFormattingClientCapabilities:
    dynamicRegistration: Optional[bool] = field(default=None)

@dataclass
class DocumentHighlightClientCapabilities:
    dynamicRegistration: Optional[bool] = field(default=None)

@dataclass
class DocumentLinkClientCapabilities:
    dynamicRegistration: Optional[bool] = field(default=None)
    tooltipSupport: Optional[bool] = field(default=None)

@dataclass
class DocumentLinkOptions:
    resolveProvider: Optional[bool] = field(default=None)

@dataclass
class DocumentRangeFormattingClientCapabilities:
    dynamicRegistration: Optional[bool] = field(default=None)

@dataclass
class DocumentOnTypeFormattingClientCapabilities:
    dynamicRegistration: Optional[bool] = field(default=None)

@dataclass
class DocumentOnTypeFormattingOptions:
    firstTriggerCharacter: str
    moreTriggerCharacter: Optional[List[str]] = field(default=None)

@dataclass
class DocumentSymbolClientCapabilities:
    dynamicRegistration: Optional[bool] = field(default=None)
    hierarchicalDocumentSymbolSupport: Optional[bool] = field(default=None)
    symbolKind: Optional[SymbolKindCapabilities] = field(default=None)


@dataclass
class DiagnosticTagCapabilities:
    valueSet: List[DiagnosticTag] = field(default_factory=list)

@dataclass
class DidChangeConfigurationClientCapabilities:
    dynamicRegistration: Optional[bool] = field(default=None)


@dataclass
class DidChangeWatchedFilesClientCapabilities:
    dynamicRegistration: Optional[bool] = field(default=None)


@dataclass
class ExecuteCommandClientCapabilities:
    dynamicRegistration: Optional[bool] = field(default=None)

@dataclass
class ExecuteCommandOptions:
    commands: List[str]

@dataclass
class FoldingRangeClientCapabilities:
    dynamicRegistration: Optional[bool] = field(default=None)
    lineFoldingOnly: Optional[bool] = field(default=None)
    rangeLimit: Optional[int] = field(default=None)

@dataclass
class HoverClientCapabilities:
    contentFormat: Optional[List[MarkupKind]] = field(default_factory=list)
    dynamicRegistration: Optional[bool] = field(default=None)

@dataclass
class ImplementationClientCapabilities:
    dynamicRegistration: Optional[bool] = field(default=None)
    linkSupport: Optional[bool] = field(default=None)

@dataclass
class ParameterCapabilities:
    labelOffsetSupport: Optional[bool] = field(default=None)

@dataclass
class PublishDiagnosticsClientCapabilities:
    relatedInformation: Optional[bool] = field(default=None)
    tagSupport: Optional[DiagnosticTagCapabilities] = field(default=None)
    versionSupport: Optional[bool] = field(default=None)

@dataclass
class ReferenceClientCapabilities:
    dynamicRegistration: Optional[bool] = field(default=None)

@dataclass
class RenameClientCapabilities:
    dynamicRegistration: Optional[bool] = field(default=None)
    prepareSupport: Optional[bool] = field(default=None)

@dataclass
class RenameOptions:
    prepareProvider: Optional[bool] = field(default=None)

@dataclass
class SelectionRangeClientCapabilities:
    dynamicRegistration: Optional[bool] = field(default=None)

@dataclass
class SignatureCapabilities:
    contextSupport: Optional[bool] = field(default=None)
    documentationFormat: Optional[List[MarkupKind]] = field(default_factory=list)
    parameterInformation: Optional[ParameterCapabilities] = field(default=None)

@dataclass
class SignatureHelpClientCapabilities:
    contextSupport: Optional[bool] = field(default=None)
    dynamicRegistration: Optional[bool] = field(default=None)
    signatureInformation: Optional[SignatureCapabilities] = field(default=None)

@dataclass
class SignatureHelpOptions:
    triggerCharacters: Optional[List[str]] = field(default=None)
    retriggerCharacters: Optional[List[str]] = field(default=None)

@dataclass
class SymbolKindCapabilities:
    valueSet: Optional[List[SymbolKind]] = field(default_factory=list)


@dataclass
class TextDocumentSyncClientCapabilities:
    didSave: Optional[bool] = field(default=None)
    dynamicRegistration: Optional[bool] = field(default=None)
    willSave: Optional[bool] = field(default=None)
    willSaveWaitUntil: Optional[bool] = field(default=None)

@dataclass
class TextDocumentSyncOptions:
    openClose: Optional[bool] = field(default=None)
    change: Optional[TexrDocumentSyncKind] = field(default=None)

@dataclass
class TypeDefinitionClientCapabilities:
    dynamicRegistration: Optional[bool] = field(default=None)
    linkSupport: Optional[bool] = field(default=None)

@dataclass
class WindowClientCapabilities:
    workDoneProgress: Optional[bool] = field(default=None)

@dataclass
class WorkspaceEditClientCapabilities:
    """Ways in which a client's workspace can be manipulated."""

    # fmt: off
    documentChanges: Optional[bool] = field(default=None)
    failureHandling: Optional[FailureHandlingKind] = field(default=None)
    resourceOperations: Optional[List[ResourceOperationKind]] = field(default_factory=list)
    # fmt: on

@dataclass
class WorkspaceFoldersServerCapabilities:
    supported: Optional[bool] = field(default=None)
    changeNotifications: Optional[Union[str, bool]] = field(default=None)

@dataclass
class WorkspaceSymbolClientCapabilities:
    dynamicRegistration: Optional[bool] = field(default=None)
    symbolKind: Optional[SymbolKindCapabilities] = field(default=None)


@dataclass
class WorkspaceClientCapabilities:
    """Specification of what the client's workspace is capable of."""

    # fmt: off
    applyEdit: Optional[bool] = field(default=None)
    configuration: Optional[bool] = field(default=None)
    didChangeConfiguration: Optional[DidChangeConfigurationClientCapabilities] = field(default=None)
    didChangeWatchedFiles: Optional[DidChangeWatchedFilesClientCapabilities] = field(default=None)
    executeCommand: Optional[ExecuteCommandClientCapabilities] = field(default=None)
    symbol: Optional[WorkspaceSymbolClientCapabilities] = field(default=None)
    workspaceEdit: Optional[WorkspaceEditClientCapabilities] = field(default=None)
    workspaceFolders: Optional[bool] = field(default=None)
    # fmt: on

@dataclass
class WorkspaceServerCapabilities:
    workspaceFolders: Optional[WorkspaceFoldersServerCapabilities] = field(default=None)

@dataclass
class WorkspaceFolder:
    uri: DocumentUri
    name: str

@dataclass
class TextDocumentClientCapabilities:
    """Specification of what the client's text document capabilities are capable of."""

    # fmt: off
    codeAction: Optional[CodeActionClientCapabilities] = field(default=None)
    codeLens: Optional[CodeLensClientCapabilities] = field(default=None)
    colorProvider: Optional[DocumentColorClientCapabilities] = field(default=None)
    completion: Optional[CompletionClientCapabilities] = field(default=None)
    declaration: Optional[DeclarationClientCapabilities] = field(default=None)
    definition: Optional[DefinitionClientCapabilities] = field(default=None)
    documentHighlight: Optional[DocumentHighlightClientCapabilities] = field(default=None)
    documentLink: Optional[DocumentLinkClientCapabilities] = field(default=None)
    documentSymbol: Optional[DocumentSymbolClientCapabilities] = field(default=None)
    foldingRange: Optional[FoldingRangeClientCapabilities] = field(default=None)
    fomatting: Optional[DocumentFormattingClientCapabilities] = field(default=None)
    hover: Optional[HoverClientCapabilities] = field(default=None)
    implementation: Optional[ImplementationClientCapabilities] = field(default=None)
    onTypeFormatting: Optional[DocumentOnTypeFormattingClientCapabilities] = field(default=None)
    publishDiagnostics: Optional[PublishDiagnosticsClientCapabilities] = field(default=None)
    rangeFormatting: Optional[DocumentRangeFormattingClientCapabilities] = field(default=None)
    references: Optional[ReferenceClientCapabilities] = field(default=None)
    rename: Optional[RenameClientCapabilities] = field(default=None)
    selectionRange: Optional[SelectionRangeClientCapabilities] = field(default=None)
    signatureHelp: Optional[SignatureHelpClientCapabilities] = field(default=None)
    synchronization: Optional[TextDocumentSyncClientCapabilities] = field(default=None)
    typeDefinition: Optional[TypeDefinitionClientCapabilities] = field(default=None)
    # fmt: on


@dataclass
class ClientCapabilities:
    """Represents features the client is able to provide."""

    experimental: Optional[Any] = field(default=None)
    textDocument: Optional[TextDocumentClientCapabilities] = field(default=None)
    window: Optional[WindowClientCapabilities] = field(default=None)
    workspace: Optional[WorkspaceClientCapabilities] = field(default=None)

@dataclass
class ServerCapabilities:
    """Represents features the server is able to provide."""

    # fmt: off
    codeActionProvider: Optional[Union[bool, CodeActionOptions]] = field(default=None)
    codeLensProvider: Optional[bool] = field(default=None)
    colorProvider: Optional[bool] = field(default=None)
    completionProvider: Optional[CompletionOptions] = field(default=None)
    declarationProvider: Optional[bool] = field(default=None)
    definitionProvider: Optional[bool] = field(default=None)
    documentFormattingProvider: Optional[bool] = field(default=None)
    documentHighlightProvider: Optional[bool] = field(default=None)
    documentLinkProvider: Optional[DocumentLinkOptions] = field(default=None)
    documentOnTypeFormattingProvider: Optional[DocumentOnTypeFormattingOptions] = field(default=None)
    documentRangeFormattingProvider: Optional[bool] = field(default=None)
    documentSymbolProvider: Optional[bool] = field(default=None)
    executeCommandProvider: Optional[ExecuteCommandOptions] = field(default=None)
    experimental: Optional[Any] = field(default=None)
    foldingRangeProvider: Optional[bool] = field(default=None)
    hoverProvider: Optional[bool] = field(default=None)
    implementationProvider: Optional[bool] = field(default=None)
    referencesProvider: Optional[bool] = field(default=None)
    renameProvider: Optional[Union[bool, RenameOptions]] = field(default=None)
    selectionRangeProvider: Optional[bool] = field(default=None)
    signatureHelpProvider: Optional[SignatureHelpOptions] = field(default=None)
    textDocumentSync: Optional[Union[int, TextDocumentSyncOptions]] = field(default=None)
    typeDefinitionProvider: Optional[bool] = field(default=None)
    workspace: Optional[WorkspaceServerCapabilities] = field(default=None)
    workspaceSymbolProvider: Optional[bool] = field(default=None)
    # fmt: on