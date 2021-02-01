import importlib
import logging

from typing import List

from pygls.features import COMPLETION, INITIALIZE, INITIALIZED, TEXT_DOCUMENT_DID_SAVE
from pygls.server import LanguageServer
from pygls.types import (
    CompletionList,
    CompletionParams,
    DidSaveTextDocumentParams,
    InitializeParams,
    Position,
)
from pygls.workspace import Document


BUILTIN_MODULES = [
    "esbonio.lsp.sphinx",
    "esbonio.lsp.completion.directives",
    "esbonio.lsp.completion.roles",
]


class RstLanguageServer(LanguageServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.logger = logging.getLogger(__name__)
        """The logger that should be used for all Language Server log entries"""

        self.app = None
        """Sphinx application instance configured for the current project."""

        self.on_init_hooks = []
        """A list of functions to run on initialization"""

        self.on_initialized_hooks = []
        """A list of functions to run after receiving the initialized notification from the
        client"""

        self.on_save_hooks = []
        """A list of hooks to run on document save."""

        self.completion_handlers = {}
        """The collection of registered completion handlers."""

    def add_feature(self, feature):
        """Add a new feature to the language server."""

        if hasattr(feature, "initialize"):
            self.on_init_hooks.append(feature.initialize)

        if hasattr(feature, "initialized"):
            self.on_initialized_hooks.append(feature.initialized)

        if hasattr(feature, "save"):
            self.on_save_hooks.append(feature.save)

        if hasattr(feature, "suggest") and hasattr(feature, "suggest_triggers"):

            for trigger in feature.suggest_triggers:
                handler = feature.suggest

                if trigger in self.completion_handlers:
                    self.completion_handlers[trigger].append(handler)
                else:
                    self.completion_handlers[trigger] = [handler]

    def load_module(self, mod: str):
        # TODO: Handle failures.
        module = importlib.import_module(mod)

        if not hasattr(module, "setup"):
            raise TypeError("Module '{}' missing setup function".format(mod))

        module.setup(self)


def get_line_til_position(doc: Document, position: Position) -> str:
    """Return the line up until the position of the cursor."""

    try:
        line = doc.lines[position.line]
    except IndexError:
        return ""

    return line[: position.character]


def create_language_server(modules: List[str]) -> RstLanguageServer:
    """Create a new language server instance.

    Parameters
    ----------
    modules:
        The list of modules that should be loaded.
    """
    import asyncio

    server = RstLanguageServer(asyncio.new_event_loop())

    for mod in modules:
        server.load_module(mod)

    @server.feature(INITIALIZE)
    def on_initialize(rst: RstLanguageServer, params: InitializeParams):

        for init_hook in rst.on_init_hooks:
            init_hook()

        rst.logger.info("LSP Server Initialized")

    @server.feature(INITIALIZED)
    def on_initialized(rst: RstLanguageServer, params):

        for initialized_hook in rst.on_initialized_hooks:
            initialized_hook()

    @server.feature(COMPLETION, trigger_characters=[".", ":", "`", "<"])
    def on_completion(rst: RstLanguageServer, params: CompletionParams):
        """Suggest completions based on the current context."""
        uri = params.textDocument.uri
        pos = params.position

        doc = rst.workspace.get_document(uri)
        line = get_line_til_position(doc, pos)

        items = []

        for pattern, handlers in rst.completion_handlers.items():
            match = pattern.match(line)
            if match:
                for handler in handlers:
                    items += handler(match, doc, pos)

        return CompletionList(False, items)

    @server.feature(TEXT_DOCUMENT_DID_SAVE)
    def on_save(rst: RstLanguageServer, params: DidSaveTextDocumentParams):

        for on_save_hook in rst.on_save_hooks:
            on_save_hook(params)

    return server
