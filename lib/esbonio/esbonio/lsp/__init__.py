import enum
import importlib
import json
import logging
import pathlib
import textwrap
from typing import List
from typing import Optional
from urllib.parse import unquote
from urllib.parse import urlparse

from pydantic import BaseModel
from pydantic import Field
from pygls.lsp.methods import COMPLETION
from pygls.lsp.methods import INITIALIZE
from pygls.lsp.methods import INITIALIZED
from pygls.lsp.methods import TEXT_DOCUMENT_DID_OPEN
from pygls.lsp.methods import TEXT_DOCUMENT_DID_SAVE
from pygls.lsp.types import CompletionList
from pygls.lsp.types import CompletionOptions
from pygls.lsp.types import CompletionParams
from pygls.lsp.types import DidOpenTextDocumentParams
from pygls.lsp.types import DidSaveTextDocumentParams
from pygls.lsp.types import InitializedParams
from pygls.lsp.types import InitializeParams
from pygls.lsp.types import Position
from pygls.server import LanguageServer
from pygls.workspace import Document
from sphinx.application import Sphinx

from esbonio.lsp.logger import LOG_LEVELS
from esbonio.lsp.logger import LogFilter
from esbonio.lsp.logger import LspHandler

__version__ = "0.6.2"


BUILTIN_MODULES = [
    "esbonio.lsp.sphinx",
    "esbonio.lsp.directives",
    "esbonio.lsp.roles",
    "esbonio.lsp.intersphinx",
    "esbonio.lsp.filepaths",
]


class SphinxConfig(BaseModel):
    """Represents both the current Sphinx configuration and also the config options that
    we should create Sphinx with."""

    version: Optional[str]
    """Sphinx's version number."""

    conf_dir: Optional[str] = Field(None, alias="confDir")
    """Can be used to override the default conf.py discovery mechanism."""

    src_dir: Optional[str] = Field(None, alias="srcDir")
    """Can be used to override the default assumption on where the project's rst files are
    located."""

    build_dir: Optional[str] = Field(None, alias="buildDir")
    """Can be used to override the default location for storing build outputs."""

    builder_name: str = Field("html", alias="builderName")
    """The currently used builder."""


class ServerConfig(BaseModel):
    """Configuration options for the server."""

    log_level: Optional[str] = Field("error", alias="logLevel")
    """The logging level for server messages"""

    log_filter: Optional[List[str]] = Field(None, alias="logFilter")
    """A list of logger names to restrict output to."""

    hide_sphinx_output: Optional[bool] = Field(False, alias="hideSphinxOutput")
    """A flag to indicate if Sphinx build output should be omitted from the log."""


class InitializationOptions(BaseModel):
    """The initialization options we can expect to receive from a client."""

    sphinx: Optional[SphinxConfig] = Field(default_factory=SphinxConfig)
    """The ``esbonio.sphinx.*`` namespace of options"""

    server: Optional[ServerConfig] = Field(default_factory=ServerConfig)
    """The ``esbonio.server.*`` namespace of options"""


class LanguageFeature:
    """Base class for language features."""

    def __init__(self, rst: "RstLanguageServer"):
        self.rst = rst
        self.logger = rst.logger.getChild(self.__class__.__name__)


class RstLanguageServer(LanguageServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.logger = logging.getLogger(__name__)
        """The logger that should be used for all Language Server log entries"""

        self.app: Optional[Sphinx] = None
        """Sphinx application instance configured for the current project."""

        self.on_initialize_hooks = []
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
            self.on_initialize_hooks.append(feature.initialize)

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

    def _configure_logging(self, config: ServerConfig):
        level = LOG_LEVELS[config.log_level]

        lsp_logger = logging.getLogger("esbonio.lsp")
        lsp_logger.setLevel(level)

        lsp_handler = LspHandler(self)
        lsp_handler.setLevel(level)

        if config.log_filter is not None and len(config.log_filter) > 0:
            lsp_handler.addFilter(LogFilter(config.log_filter))

        formatter = logging.Formatter("[%(name)s] %(message)s")
        lsp_handler.setFormatter(formatter)
        lsp_logger.addHandler(lsp_handler)

        if not config.hide_sphinx_output:
            sphinx_logger = logging.getLogger("esbonio.sphinx")
            sphinx_logger.setLevel(logging.INFO)

            sphinx_handler = LspHandler(self)
            sphinx_handler.setLevel(logging.INFO)

            formatter = logging.Formatter("%(message)s")
            sphinx_handler.setFormatter(formatter)
            sphinx_logger.addHandler(sphinx_handler)


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


def create_language_server(modules: List[str]) -> RstLanguageServer:
    """Create a new language server instance.

    Parameters
    ----------
    modules:
        The list of modules that should be loaded.
    """
    server = RstLanguageServer()

    for mod in modules:
        server.load_module(mod)

    @server.feature(INITIALIZE)
    def on_initialize(rst: RstLanguageServer, params: InitializeParams):
        options = InitializationOptions(**params.initialization_options)

        # Let there be light...
        rst._configure_logging(options.server)
        rst.logger.info("Language server started.")

        rst.logger.debug("%s: %s", INITIALIZE, dump(params))
        rst.run_hooks("initialize", options)

    @server.feature(INITIALIZED)
    def on_initialized(rst: RstLanguageServer, params: InitializedParams):
        rst.logger.debug("%s: %s", INITIALIZED, dump(params))
        rst.run_hooks("initialized")

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

    @server.feature("$/setTraceNotification")
    def vscode_set_trace(rst: RstLanguageServer, params):
        """Dummy implementation, stops JsonRpcMethodNotFound exceptions."""
        rst.logger.debug("$/setTraceNotification: %s", dump(params))

    return server
