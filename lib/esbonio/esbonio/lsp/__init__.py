import enum
import importlib
import json
import logging
import textwrap
import traceback
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Type

from pygls.lsp.methods import CODE_ACTION
from pygls.lsp.methods import COMPLETION
from pygls.lsp.methods import COMPLETION_ITEM_RESOLVE
from pygls.lsp.methods import DEFINITION
from pygls.lsp.methods import DOCUMENT_LINK
from pygls.lsp.methods import DOCUMENT_SYMBOL
from pygls.lsp.methods import HOVER
from pygls.lsp.methods import IMPLEMENTATION
from pygls.lsp.methods import INITIALIZE
from pygls.lsp.methods import INITIALIZED
from pygls.lsp.methods import SHUTDOWN
from pygls.lsp.methods import TEXT_DOCUMENT_DID_CHANGE
from pygls.lsp.methods import TEXT_DOCUMENT_DID_OPEN
from pygls.lsp.methods import TEXT_DOCUMENT_DID_SAVE
from pygls.lsp.methods import WORKSPACE_DID_DELETE_FILES
from pygls.lsp.types import CodeActionParams
from pygls.lsp.types import CompletionItem
from pygls.lsp.types import CompletionList
from pygls.lsp.types import CompletionOptions
from pygls.lsp.types import CompletionParams
from pygls.lsp.types import DefinitionParams
from pygls.lsp.types import DeleteFilesParams
from pygls.lsp.types import DidChangeTextDocumentParams
from pygls.lsp.types import DidOpenTextDocumentParams
from pygls.lsp.types import DidSaveTextDocumentParams
from pygls.lsp.types import DocumentLinkParams
from pygls.lsp.types import DocumentSymbolParams
from pygls.lsp.types import FileOperationFilter
from pygls.lsp.types import FileOperationPattern
from pygls.lsp.types import FileOperationRegistrationOptions
from pygls.lsp.types import Hover
from pygls.lsp.types import HoverParams
from pygls.lsp.types import ImplementationParams
from pygls.lsp.types import InitializedParams
from pygls.lsp.types import InitializeParams
from pygls.lsp.types import MarkupContent
from pygls.lsp.types import MarkupKind
from pygls.lsp.types import ServerCapabilities
from pygls.protocol import LanguageServerProtocol

from .rst import CompletionContext
from .rst import DefinitionContext
from .rst import DocumentLinkContext
from .rst import HoverContext
from .rst import ImplementationContext
from .rst import LanguageFeature
from .rst import RstLanguageServer
from .symbols import SymbolVisitor

__version__ = "0.15.0"

__all__ = [
    "CompletionContext",
    "DefinitionContext",
    "DocumentLinkContext",
    "HoverContext",
    "ImplementationContext",
    "LanguageFeature",
    "RstLanguageServer",
    "create_language_server",
]

logger = logging.getLogger(__name__)

# Commands
ESBONIO_SERVER_CONFIGURATION = "esbonio.server.configuration"
ESBONIO_SERVER_PREVIEW = "esbonio.server.preview"
ESBONIO_SERVER_BUILD = "esbonio.server.build"


class Patched(LanguageServerProtocol):
    """Tweaked version of the protocol allowing us to tweak how the `ServerCapabilities`
    are constructed."""

    def __init__(self, *args, **kwargs):
        self._server_capabilities = ServerCapabilities()
        super().__init__(*args, **kwargs)

    @property
    def server_capabilities(self):
        return self._server_capabilities

    @server_capabilities.setter
    def server_capabilities(self, value: ServerCapabilities):

        if WORKSPACE_DID_DELETE_FILES in self.fm.features:
            opts = self.fm.feature_options.get(WORKSPACE_DID_DELETE_FILES, None)
            if opts:
                value.workspace.file_operations.did_delete = opts  # type: ignore

        self._server_capabilities = value


def create_language_server(
    server_cls: Type[RstLanguageServer], modules: Iterable[str], *args, **kwargs
) -> RstLanguageServer:
    """Create a new language server instance.

    Parameters
    ----------
    server_cls:
       The class definition to create the server from.
    modules:
       The list of modules that should be loaded.
    args, kwargs:
       Any additional arguments that should be passed to the language server's
       constructor.
    """

    if "logger" not in kwargs:
        kwargs["logger"] = logger

    try:
        server = server_cls(*args, **kwargs, protocol_cls=Patched)
    except TypeError:
        # Work around older version of pygls on Python 3.6
        kwargs.pop("name", None)
        kwargs.pop("version", None)

        server = server_cls(*args, **kwargs, protocol_cls=Patched)

    for module in modules:
        _load_module(server, module)

    return _configure_lsp_methods(server)


def _configure_lsp_methods(server: RstLanguageServer) -> RstLanguageServer:
    @server.feature(INITIALIZE)
    def on_initialize(ls: RstLanguageServer, params: InitializeParams):
        ls.initialize(params)

        for feature in ls._features.values():
            feature.initialize(params)

    @server.feature(INITIALIZED)
    def on_initialized(ls: RstLanguageServer, params: InitializedParams):
        ls.initialized(params)

        for feature in ls._features.values():
            feature.initialized(params)

    @server.feature(SHUTDOWN)
    def on_shutdown(ls: RstLanguageServer, *args):
        ls.on_shutdown(*args)

        for feature in ls._features.values():
            feature.on_shutdown(*args)

    @server.feature(TEXT_DOCUMENT_DID_OPEN)
    def on_open(ls: RstLanguageServer, params: DidOpenTextDocumentParams):

        # TODO: Delete me when we've dropped Python 3.6 and a pygls release that
        # remembers the language id is available.
        doc = ls.workspace.get_document(params.text_document.uri)
        doc.language_id = params.text_document.language_id  # type: ignore

    @server.feature(TEXT_DOCUMENT_DID_CHANGE)
    def on_change(ls: RstLanguageServer, params: DidChangeTextDocumentParams):
        pass

    @server.command(ESBONIO_SERVER_BUILD)
    def build(ls: RstLanguageServer, *args):
        params = {} if not args[0] else args[0][0]._asdict()
        force_all: bool = params.get("force_all", False)
        filenames: Optional[List[str]] = params.get("filenames", None)
        ls.build(force_all, filenames)

    @server.feature(TEXT_DOCUMENT_DID_SAVE)
    def on_save(ls: RstLanguageServer, params: DidSaveTextDocumentParams):

        ls.save(params)

        for feature in ls._features.values():
            feature.save(params)

    @server.feature(
        WORKSPACE_DID_DELETE_FILES,
        FileOperationRegistrationOptions(
            filters=[
                FileOperationFilter(
                    pattern=FileOperationPattern(glob="**/*.rst"),
                )
            ]
        ),
    )
    def on_delete_files(ls: RstLanguageServer, params: DeleteFilesParams):
        ls.delete_files(params)

        for feature in ls._features.values():
            feature.delete_files(params)

    @server.feature(CODE_ACTION)
    def on_code_action(ls: RstLanguageServer, params: CodeActionParams):
        actions = []

        for feature in ls._features.values():
            actions += feature.code_action(params)

        return actions

    @server.feature(HOVER)
    def on_hover(ls: RstLanguageServer, params: HoverParams):
        uri = params.text_document.uri
        doc = ls.workspace.get_document(uri)
        pos = params.position
        line = ls.line_at_position(doc, pos)
        location = ls.get_location_type(doc, pos)

        hover_values = []
        for feature in ls._features.values():
            for pattern in feature.hover_triggers:
                for match in pattern.finditer(line):
                    if not match:
                        continue

                    # only trigger hover if the position of the request is within
                    # the match
                    start, stop = match.span()
                    if start <= pos.character <= stop:
                        context = HoverContext(
                            doc=doc,
                            location=location,
                            match=match,
                            position=pos,
                            capabilities=ls.client_capabilities,
                        )
                        ls.logger.debug("Hover context: %s", context)

                        hover_value = feature.hover(context)
                        hover_values.append(hover_value)

        hover_content_values = "\n".join(hover_values)

        return Hover(
            contents=MarkupContent(
                kind=MarkupKind.Markdown,
                value=hover_content_values,
            )
        )

    # <engine-example>
    @server.feature(
        COMPLETION,
        CompletionOptions(
            trigger_characters=[">", ".", ":", "`", "<", "/"], resolve_provider=True
        ),
    )
    def on_completion(ls: RstLanguageServer, params: CompletionParams):
        uri = params.text_document.uri
        pos = params.position

        doc = ls.workspace.get_document(uri)
        line = ls.line_at_position(doc, pos)
        location = ls.get_location_type(doc, pos)

        items = []

        for name, feature in ls._features.items():
            for pattern in feature.completion_triggers:
                for match in pattern.finditer(line):
                    if not match:
                        continue

                    # Only trigger completions if the position of the request is within
                    # the match.
                    start, stop = match.span()
                    if start <= pos.character <= stop:
                        context = CompletionContext(
                            doc=doc,
                            location=location,
                            match=match,
                            position=pos,
                            capabilities=ls.client_capabilities,
                        )
                        ls.logger.debug("Completion context: %s", context)

                        for item in feature.complete(context):
                            item.data = {"source_feature": name, **(item.data or {})}
                            items.append(item)

        return CompletionList(is_incomplete=False, items=items)

    # </engine-example>

    @server.feature(COMPLETION_ITEM_RESOLVE)
    def on_completion_resolve(
        ls: RstLanguageServer, item: CompletionItem
    ) -> CompletionItem:
        source = (item.data or {}).get("source_feature", "")
        feature = ls.get_feature(source)

        if not feature:
            ls.logger.error(
                "Unable to resolve completion item, unknown source: '%s'", source
            )
            return item

        return feature.completion_resolve(item)

    @server.feature(DEFINITION)
    def on_definition(ls: RstLanguageServer, params: DefinitionParams):
        uri = params.text_document.uri
        pos = params.position

        doc = ls.workspace.get_document(uri)
        line = ls.line_at_position(doc, pos)
        location = ls.get_location_type(doc, pos)

        definitions = []

        for feature in ls._features.values():
            for pattern in feature.definition_triggers:
                for match in pattern.finditer(line):
                    if not match:
                        continue

                    start, stop = match.span()
                    if start <= pos.character and pos.character <= stop:
                        context = DefinitionContext(
                            doc=doc, location=location, match=match, position=pos
                        )
                        definitions += feature.definition(context)

        return definitions

    @server.feature(IMPLEMENTATION)
    def on_implementation(ls: RstLanguageServer, params: ImplementationParams):
        uri = params.text_document.uri
        pos = params.position

        doc = ls.workspace.get_document(uri)
        line = ls.line_at_position(doc, pos)
        location = ls.get_location_type(doc, pos)

        implementations = []

        for feature in ls._features.values():
            for pattern in feature.implementation_triggers:
                for match in pattern.finditer(line):
                    if not match:
                        continue

                    start, stop = match.span()
                    if start <= pos.character and pos.character <= stop:
                        context = ImplementationContext(
                            doc=doc, location=location, match=match, position=pos
                        )
                        ls.logger.debug("Implementation context: %s", context)
                        implementations += feature.implementation(context)

        return implementations

    @server.feature(DOCUMENT_LINK)
    def on_document_link(ls: RstLanguageServer, params: DocumentLinkParams):
        uri = params.text_document.uri
        doc = ls.workspace.get_document(uri)
        context = DocumentLinkContext(doc=doc, capabilities=ls.client_capabilities)

        links = []
        for feature in ls._features.values():
            links += feature.document_link(context) or []

        return links

    @server.feature(DOCUMENT_SYMBOL)
    def on_document_symbol(ls: RstLanguageServer, params: DocumentSymbolParams):

        doctree = ls.get_initial_doctree(uri=params.text_document.uri)
        if doctree is None:
            return []

        visitor = SymbolVisitor(ls, doctree)
        doctree.walkabout(visitor)

        return visitor.symbols

    @server.command(ESBONIO_SERVER_CONFIGURATION)
    def get_configuration(ls: RstLanguageServer, *args):
        """Get the server's configuration.

        Not to be confused with the ``workspace/configuration`` request where the server
        can request the client's configuration. This is so clients can ask for sphinx's
        output path for example.

        As far as I know, there isn't anything built into the spec to cater for this?
        """
        config = ls.configuration
        ls.logger.debug("%s: %s", ESBONIO_SERVER_CONFIGURATION, dump(config))

        return config

    @server.command(ESBONIO_SERVER_PREVIEW)
    def preview(ls: RstLanguageServer, *args) -> Dict[str, Any]:
        """Start/Generate a preview of the project"""
        params = {} if not args[0] else args[0][0]._asdict()
        ls.logger.debug("%s: %s", ESBONIO_SERVER_PREVIEW, params)

        return ls.preview(params) or {}

    return server


def _load_module(server: RstLanguageServer, modname: str):
    """Load an extension module by calling its ``esbonio_setup`` function, if it exists."""

    try:
        module = importlib.import_module(modname)
    except ImportError:
        logger.error(
            "Unable to import module '%s'\n%s", modname, traceback.format_exc()
        )
        return None

    setup = getattr(module, "esbonio_setup", None)
    if setup is None:
        logger.error("Skipping module '%s', missing 'esbonio_setup' function", modname)
        return None

    server.load_extension(modname, setup)


def dump(obj) -> str:
    """Debug helper function that converts an object to JSON."""

    def default(o):
        if isinstance(o, enum.Enum):
            return o.value

        fields = {}
        for k, v in o.__dict__.items():

            if v is None:
                continue

            # Truncate long strings - but not uris!
            if isinstance(v, str) and not k.lower().endswith("uri"):
                v = textwrap.shorten(v, width=25)

            fields[k] = v

        return fields

    return json.dumps(obj, default=default)
