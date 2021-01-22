import importlib
import logging

from pygls.features import COMPLETION, INITIALIZED, TEXT_DOCUMENT_DID_SAVE
from pygls.server import LanguageServer
from pygls.types import (
    CompletionList,
    CompletionParams,
    DidSaveTextDocumentParams,
    InitializeParams,
    Position,
)
from pygls.workspace import Document


class RstLanguageServer(LanguageServer):
    def __init__(self):
        super().__init__()

        self.logger = logging.getLogger(__name__)
        """The logger that should be used for all Language Server log entries"""

        self.app = None
        """Sphinx application instance configured for the current project."""

        self.on_init_hooks = []
        """A list of functions to run on initialization"""

        self.on_save_hooks = []
        """A list of hooks to run on document save."""

        self.completion_handlers = {}
        """The collection of registered completion handlers."""

    def add_feature(self, feature):
        """Add a new feature to the language server."""

        if hasattr(feature, "initialize"):
            self.on_init_hooks.append(feature.initialize)

        if hasattr(feature, "save"):
            self.on_save_hooks.append(feature.save)

        # TODO: Add support for mutltiple handlers using the same trigger.
        if hasattr(feature, "suggest") and hasattr(feature, "suggest_trigger"):
            trigger = feature.suggest_trigger
            handler = feature.suggest

            self.completion_handlers[trigger] = handler

    def load_module(self, mod: str):
        # TODO: Handle failures.
        module = importlib.import_module(mod)

        if not hasattr(module, "setup"):
            raise TypeError("Module '{}' missing setup function".format(mod))

        module.setup(self)


# TODO: Rethink how we do startup, should esbonio.__main__ be doing this?
server = RstLanguageServer()
builtin_modules = [
    "esbonio.lsp.sphinx",
    "esbonio.lsp.completion.directives",
    "esbonio.lsp.completion.roles",
]


@server.feature(INITIALIZED)
def on_initialized(rst: RstLanguageServer, params: InitializeParams):

    for mod in builtin_modules:
        rst.load_module(mod)

    for init_hook in rst.on_init_hooks:
        init_hook()

    rst.logger.info("LSP Server Initialized")


def get_line_til_position(doc: Document, position: Position) -> str:
    """Return the line up until the position of the cursor."""

    try:
        line = doc.lines[position.line]
    except IndexError:
        return ""

    return line[: position.character]


@server.feature(COMPLETION, trigger_characters=[".", ":", "`", "<"])
def on_completion(rst: RstLanguageServer, params: CompletionParams):
    """Suggest completions based on the current context."""
    uri = params.textDocument.uri
    pos = params.position

    doc = rst.workspace.get_document(uri)
    line = get_line_til_position(doc, pos)

    items = []

    for pattern, handler in rst.completion_handlers.items():
        match = pattern.match(line)
        if match:
            items += handler(match, line, doc)

    return CompletionList(False, items)


@server.feature(TEXT_DOCUMENT_DID_SAVE)
def on_save(rst: RstLanguageServer, params: DidSaveTextDocumentParams):

    for on_save_hook in rst.on_save_hooks:
        on_save_hook(params)
