import enum
import importlib
import json
import logging
import pathlib

from typing import List, Optional
from urllib.parse import urlparse, unquote

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
from sphinx.application import Sphinx


BUILTIN_MODULES = [
    "esbonio.lsp.sphinx",
    "esbonio.lsp.directives",
    "esbonio.lsp.roles",
    "esbonio.lsp.intersphinx",
]


class LanguageFeature:
    """Base class for language features."""

    def __init__(self, rst: "RstLanguageServer"):
        self.rst = rst
        self.logger = rst.logger.getChild(self.__class__.__name__)


class RstLanguageServer(LanguageServer):
    def __init__(self, cache_dir=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.cache_dir = cache_dir
        """The folder to store cached data in."""

        self.logger = logging.getLogger(__name__)
        """The logger that should be used for all Language Server log entries"""

        self.app: Optional[Sphinx] = None
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

    def run_hooks(self, kind: str, *args):
        """Run each hook registered of the given kind."""

        hooks = getattr(self, f"on_{kind}_hooks")
        for hook in hooks:
            hook(*args)


def get_line_til_position(doc: Document, position: Position) -> str:
    """Return the line up until the position of the cursor."""

    try:
        line = doc.lines[position.line]
    except IndexError:
        return ""

    return line[: position.character]


def dump(obj) -> str:
    """Debug helper function that converts an object to JSON."""

    def default(obj):
        if isinstance(obj, enum.Enum):
            return obj.value

        return {k: v for k, v in obj.__dict__.items() if v is not None}

    return json.dumps(obj, default=default)


def create_language_server(
    modules: List[str], cache_dir: Optional[str] = None
) -> RstLanguageServer:
    """Create a new language server instance.

    Parameters
    ----------
    modules:
        The list of modules that should be loaded.
    cache_dir:
        The folder to use for cached data.
    """
    server = RstLanguageServer(cache_dir)

    for mod in modules:
        server.load_module(mod)

    @server.feature(INITIALIZE)
    def on_initialize(rst: RstLanguageServer, params: InitializeParams):

        rst.run_hooks("init")
        rst.logger.info("LSP Server Initialized")

    @server.feature(INITIALIZED)
    def on_initialized(rst: RstLanguageServer, params):
        rst.run_hooks("initialized")

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
        rst.logger.debug("DidSave: %s", params)

        uri = urlparse(params.textDocument.uri)
        filepath = pathlib.Path(unquote(uri.path))
        conf_py = pathlib.Path(rst.app.confdir, "conf.py")

        # Re-initialize everything if the app's config has changed.
        if filepath == conf_py:
            rst.run_hooks("init")
        else:
            rst.run_hooks("save", params)

    @server.feature("$/setTraceNotification")
    def vscode_set_trace(rst: RstLanguageServer, params):
        """Dummy implementation, stops JsonRpcMethodNotFound exceptions."""
        rst.logger.debug("VSCode set trace: %s", params)

    return server
