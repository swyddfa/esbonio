import enum
import importlib
import json
import logging
import pathlib
import textwrap

from typing import List, Optional
from urllib.parse import urlparse, unquote

from pygls.server import LanguageServer
from pygls.lsp.methods import (
    COMPLETION,
    INITIALIZE,
    INITIALIZED,
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_DID_SAVE,
)
from pygls.lsp.types import (
    CompletionList,
    CompletionOptions,
    CompletionParams,
    ConfigurationItem,
    ConfigurationParams,
    DidOpenTextDocumentParams,
    DidSaveTextDocumentParams,
    InitializeParams,
    InitializedParams,
    Position,
)
from pygls.workspace import Document
from sphinx.application import Sphinx

__version__ = "0.6.1"


BUILTIN_MODULES = [
    "esbonio.lsp.sphinx",
    "esbonio.lsp.directives",
    "esbonio.lsp.roles",
    "esbonio.lsp.intersphinx",
    "esbonio.lsp.filepaths",
]


class LanguageFeature:
    """Base class for language features."""

    def __init__(self, rst: "RstLanguageServer"):
        self.rst = rst
        self.logger = rst.logger.getChild(self.__class__.__name__)


class SphinxConfig:
    """Represents the `esbonio.sphinx.*` configuration namespace."""

    def __init__(self, conf_dir: Optional[str] = None, src_dir: Optional[str] = None):
        self.conf_dir = conf_dir
        """Used to override the default 'conf.py' discovery mechanism."""

        self.src_dir = src_dir
        """Used to override the assumption that rst soruce files are
        in the same folder as 'conf.py'"""

    @classmethod
    def default(cls):
        return cls(conf_dir="", src_dir="")

    @classmethod
    def from_dict(cls, config):
        conf_dir = config.get("confDir", "")
        src_dir = config.get("srcDir", "")

        return cls(conf_dir=conf_dir, src_dir=src_dir)


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
            self.logger.debug("Running '%s' hook %s", kind, hook)
            hook(*args)


def get_line_til_position(doc: Document, position: Position) -> str:
    """Return the line up until the position of the cursor."""

    try:
        line = doc.lines[position.line]
    except IndexError:
        return ""

    return line[: position.character]


def filepath_from_uri(uri: str) -> pathlib.Path:
    """Given a uri, return the filepath component."""

    uri = urlparse(uri)
    return pathlib.Path(unquote(uri.path))


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
        rst.logger.debug("%s: %s", INITIALIZE, dump(params))
        rst.run_hooks("init")

        rst.logger.info("Language server started.")

    @server.feature(INITIALIZED)
    async def on_initialized(rst: RstLanguageServer, params: InitializedParams):
        rst.logger.debug("%s: %s", INITIALIZED, dump(params))

        config_params = ConfigurationParams(
            items=[ConfigurationItem(section="esbonio.sphinx")]
        )

        config_items = await rst.get_configuration_async(config_params)
        sphinx_config = SphinxConfig.from_dict(config_items[0] or dict())

        rst.logger.debug("SphinxConfig: %s", dump(sphinx_config))
        rst.run_hooks("initialized", sphinx_config)

        rst.logger.info("LSP server initialized")

    @server.feature(
        COMPLETION, CompletionOptions(trigger_characters=[".", ":", "`", "<", "/"])
    )
    def on_completion(rst: RstLanguageServer, params: CompletionParams):
        """Suggest completions based on the current context."""
        rst.logger.debug("%s: %s", COMPLETION, dump(params))

        uri = params.text_document.uri
        pos = params.position

        doc = rst.workspace.get_document(uri)
        line = get_line_til_position(doc, pos)

        items = []

        for pattern, handlers in rst.completion_handlers.items():
            match = pattern.match(line)
            if match:
                for handler in handlers:
                    items += handler(match, doc, pos)

        return CompletionList(is_incomplete=False, items=items)

    @server.feature(TEXT_DOCUMENT_DID_OPEN)
    def on_open(rst: RstLanguageServer, params: DidOpenTextDocumentParams):
        rst.logger.debug("%s: %s", TEXT_DOCUMENT_DID_OPEN, dump(params))

    @server.feature(TEXT_DOCUMENT_DID_SAVE)
    def on_save(rst: RstLanguageServer, params: DidSaveTextDocumentParams):
        rst.logger.debug("%s: %s", TEXT_DOCUMENT_DID_SAVE, dump(params))
        rst.run_hooks("save", params)

    @server.feature("$/setTrace")
    def on_set_trace(rst: RstLanguageServer, params):
        """Dummy implementation, stops JsonRpcMethodNotFound exceptions."""
        rst.logger.debug("$/setTrace: %s", dump(params))

    @server.feature("$/setTraceNotification")
    def vscode_set_trace(rst: RstLanguageServer, params):
        """Dummy implementation, stops JsonRpcMethodNotFound exceptions."""
        rst.logger.debug("$/setTraceNotification: %s", dump(params))

    return server
