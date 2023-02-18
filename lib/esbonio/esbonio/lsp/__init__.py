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

from lsprotocol.types import COMPLETION_ITEM_RESOLVE
from lsprotocol.types import INITIALIZE
from lsprotocol.types import INITIALIZED
from lsprotocol.types import SHUTDOWN
from lsprotocol.types import TEXT_DOCUMENT_CODE_ACTION
from lsprotocol.types import TEXT_DOCUMENT_COMPLETION
from lsprotocol.types import TEXT_DOCUMENT_DEFINITION
from lsprotocol.types import TEXT_DOCUMENT_DID_CHANGE
from lsprotocol.types import TEXT_DOCUMENT_DID_OPEN
from lsprotocol.types import TEXT_DOCUMENT_DID_SAVE
from lsprotocol.types import TEXT_DOCUMENT_DOCUMENT_LINK
from lsprotocol.types import TEXT_DOCUMENT_DOCUMENT_SYMBOL
from lsprotocol.types import TEXT_DOCUMENT_HOVER
from lsprotocol.types import TEXT_DOCUMENT_IMPLEMENTATION
from lsprotocol.types import WORKSPACE_DID_DELETE_FILES
from lsprotocol.types import CodeActionParams
from lsprotocol.types import CompletionItem
from lsprotocol.types import CompletionList
from lsprotocol.types import CompletionOptions
from lsprotocol.types import CompletionParams
from lsprotocol.types import DefinitionParams
from lsprotocol.types import DeleteFilesParams
from lsprotocol.types import DidChangeTextDocumentParams
from lsprotocol.types import DidOpenTextDocumentParams
from lsprotocol.types import DidSaveTextDocumentParams
from lsprotocol.types import DocumentLinkParams
from lsprotocol.types import DocumentSymbolParams
from lsprotocol.types import FileOperationFilter
from lsprotocol.types import FileOperationPattern
from lsprotocol.types import FileOperationRegistrationOptions
from lsprotocol.types import Hover
from lsprotocol.types import HoverParams
from lsprotocol.types import ImplementationParams
from lsprotocol.types import InitializedParams
from lsprotocol.types import InitializeParams
from lsprotocol.types import MarkupContent
from lsprotocol.types import MarkupKind

from .rst import CompletionContext
from .rst import DefinitionContext
from .rst import DocumentLinkContext
from .rst import HoverContext
from .rst import ImplementationContext
from .rst import LanguageFeature
from .rst import RstLanguageServer
from .symbols import SymbolVisitor

__version__ = "0.16.1"

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

    server = server_cls(*args, **kwargs)

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
        ...

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

    @server.feature(TEXT_DOCUMENT_CODE_ACTION)
    def on_code_action(ls: RstLanguageServer, params: CodeActionParams):
        actions = []

        for feature in ls._features.values():
            actions += feature.code_action(params)

        return actions

    @server.feature(TEXT_DOCUMENT_HOVER)
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
        TEXT_DOCUMENT_COMPLETION,
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
                            config=ls.user_config.server.completion,
                            capabilities=ls.client_capabilities,
                        )
                        ls.logger.debug("Completion context: %s", context)

                        for item in feature.complete(context):
                            item.data = {"source_feature": name, **(item.data or {})}  # type: ignore
                            items.append(item)

        return CompletionList(is_incomplete=False, items=items)

    # </engine-example>

    @server.feature(COMPLETION_ITEM_RESOLVE)
    def on_completion_resolve(
        ls: RstLanguageServer, item: CompletionItem
    ) -> CompletionItem:
        source = (item.data or {}).get("source_feature", "")  # type: ignore
        feature = ls.get_feature(source)

        if not feature:
            ls.logger.error(
                "Unable to resolve completion item, unknown source: '%s'", source
            )
            return item

        return feature.completion_resolve(item)

    @server.feature(TEXT_DOCUMENT_DEFINITION)
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

    @server.feature(TEXT_DOCUMENT_IMPLEMENTATION)
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

    @server.feature(TEXT_DOCUMENT_DOCUMENT_LINK)
    def on_document_link(ls: RstLanguageServer, params: DocumentLinkParams):
        uri = params.text_document.uri
        doc = ls.workspace.get_document(uri)
        context = DocumentLinkContext(doc=doc, capabilities=ls.client_capabilities)

        links = []
        for feature in ls._features.values():
            links += feature.document_link(context) or []

        return links

    @server.feature(TEXT_DOCUMENT_DOCUMENT_SYMBOL)
    def on_document_symbol(ls: RstLanguageServer, params: DocumentSymbolParams):

        doctree = ls.get_initial_doctree(uri=params.text_document.uri)
        if doctree is None:
            return None

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
        params = {} if not args[0] else args[0][0]
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
