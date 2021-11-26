import enum
import importlib
import json
import logging
import textwrap
import traceback
from typing import List

from pygls.lsp.methods import COMPLETION
from pygls.lsp.methods import DEFINITION
from pygls.lsp.methods import DOCUMENT_SYMBOL
from pygls.lsp.methods import INITIALIZE
from pygls.lsp.methods import INITIALIZED
from pygls.lsp.methods import TEXT_DOCUMENT_DID_CHANGE
from pygls.lsp.methods import TEXT_DOCUMENT_DID_OPEN
from pygls.lsp.methods import TEXT_DOCUMENT_DID_SAVE
from pygls.lsp.types import CompletionList
from pygls.lsp.types import CompletionOptions
from pygls.lsp.types import CompletionParams
from pygls.lsp.types import DefinitionParams
from pygls.lsp.types import DidChangeTextDocumentParams
from pygls.lsp.types import DidOpenTextDocumentParams
from pygls.lsp.types import DidSaveTextDocumentParams
from pygls.lsp.types import DocumentSymbolParams
from pygls.lsp.types import InitializedParams
from pygls.lsp.types import InitializeParams

from .rst import CompletionContext
from .rst import LanguageFeature
from .rst import RstLanguageServer
from .rst import SymbolVisitor
from .sphinx import SphinxLanguageServer

__version__ = "0.8.0"

__all__ = [
    "BUILTIN_MODULES",
    "LanguageFeature",
    "RstLanguageServer",
    "SphinxLanguageServer",
    "create_language_server",
]

BUILTIN_MODULES = [
    "esbonio.lsp.directives",
    "esbonio.lsp.roles",
    "esbonio.lsp.completion",
    "esbonio.lsp.definition",
]

logger = logging.getLogger(__name__)


def create_language_server(
    server_cls: RstLanguageServer, modules: List[str], *args, **kwargs
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

    @server.feature(INITIALIZE)
    def on_initialize(rst: server_cls, params: InitializeParams):
        rst.initialize(params)

        for feature in rst._features.values():
            feature.initialize(params)

    @server.feature(INITIALIZED)
    def on_initialized(rst: server_cls, params: InitializedParams):
        rst.initialized(params)

        for feature in rst._features.values():
            feature.initialized(params)

    @server.feature(TEXT_DOCUMENT_DID_OPEN)
    def on_open(rst: server_cls, params: DidOpenTextDocumentParams):
        pass

    @server.feature(TEXT_DOCUMENT_DID_CHANGE)
    def on_change(rst: server_cls, params: DidChangeTextDocumentParams):
        pass

    @server.feature(TEXT_DOCUMENT_DID_SAVE)
    def on_save(rst: server_cls, params: DidSaveTextDocumentParams):
        rst.save(params)

        for feature in rst._features.values():
            feature.save(params)

    @server.feature(
        COMPLETION, CompletionOptions(trigger_characters=[".", ":", "`", "<", "/"])
    )
    def on_completion(rst: server_cls, params: CompletionParams):
        uri = params.text_document.uri
        pos = params.position

        doc = rst.workspace.get_document(uri)
        line = rst.line_at_position(doc, pos)
        location = rst.get_location_type(doc, pos)

        items = []

        for feature in rst._features.values():
            for pattern in feature.completion_triggers:
                for match in pattern.finditer(line):
                    if not match:
                        continue

                    # Only trigger completions if the position of the request is within
                    # the match.
                    start, stop = match.span()
                    if start <= pos.character <= stop:
                        context = CompletionContext(
                            doc=doc, location=location, match=match, position=pos
                        )
                        rst.logger.debug("Completion context: %s", context)
                        items += feature.complete(context)

        return CompletionList(is_incomplete=False, items=items)

    @server.feature(DEFINITION)
    def on_definition(rst: server_cls, params: DefinitionParams):
        uri = params.text_document.uri
        pos = params.position

        doc = rst.workspace.get_document(uri)
        line = rst.line_at_position(doc, pos)

        definitions = []

        for feature in rst._features.values():
            for pattern in feature.definition_triggers:
                for match in pattern.finditer(line):
                    if not match:
                        continue

                    start, stop = match.span()
                    if start < pos.character and pos.character < stop:
                        definitions += feature.definition(match, doc, pos)

        return definitions

    @server.feature(DOCUMENT_SYMBOL)
    def on_document_symbol(rst: server_cls, params: DocumentSymbolParams):

        doctree = rst.get_doctree(uri=params.text_document.uri)
        if doctree is None:
            return []

        visitor = SymbolVisitor(rst, doctree)
        doctree.walkabout(visitor)

        return visitor.symbols

    @server.command("esbonio.server.configuration")
    def get_configuration(rst: server_cls, *args):
        """Get the server's configuration.

        Not to be confused with the ``workspace/configuration`` request where the server
        can request the client's configuration. This is so client's can ask for sphinx's
        output path for example.

        As far as I know, there isn't anything built into the spec to cater for this?
        """
        config = rst.configuration
        rst.logger.debug("%s: %s", "esbonio.server.configuration", config)

        return config

    return server


def _load_module(server: RstLanguageServer, module: str):

    try:
        mod = importlib.import_module(module)
    except ImportError:
        logger.error("Unable to import module '%s'\n%s", module, traceback.format_exc())
        return

    if not hasattr(mod, "esbonio_setup"):
        logger.error(
            "Unable to load module '%s', missing 'esbonio_setup' function", module
        )
        return

    try:
        mod.esbonio_setup(server)
    except Exception:
        logger.error(
            "Error while setting up module '%s'\n%s", module, traceback.format_exc()
        )


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
