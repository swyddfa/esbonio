import importlib
import logging
import pathlib
import re

import appdirs
import sphinx.util.console as console

from pygls.features import COMPLETION, INITIALIZED, TEXT_DOCUMENT_DID_SAVE
from pygls.server import LanguageServer
from pygls.types import (
    CompletionList,
    CompletionParams,
    Diagnostic,
    DiagnosticSeverity,
    DidSaveTextDocumentParams,
    InitializeParams,
    MessageType,
    Position,
    Range,
)
from pygls.workspace import Document
from sphinx.application import Sphinx


PROBLEM_PATTERN = re.compile(
    r"""
    (?P<file>[^:]*):(?P<line>\d+):\s(?P<type>[^:]*):(\s+)?(?P<message>.*)
    """,
    re.VERBOSE,
)
"""Regular Expression used to identify warnings/errors in Sphinx's output."""

PROBLEM_SEVERITY = {
    "WARNING": DiagnosticSeverity.Warning,
    "ERROR": DiagnosticSeverity.Error,
}


class RstLanguageServer(LanguageServer):
    def __init__(self):
        super().__init__()

        self.logger = logging.getLogger(__name__)
        """The logger that should be used for all Language Server log entries"""

        self.sphinx_log = logging.getLogger("esbonio.sphinx")
        """The logger that should be used by a Sphinx application"""

        self.app = None
        """Sphinx application instance configured for the current project."""

        self.completion_handlers = {}
        """The collection of registered completion handlers."""

        self.diagnostics = {}
        """A place to keep track of diagnostics we can publish to the client."""

    def add_completion_handler(self, pattern, handler):
        """Register a new completion handler.

        Parameters
        ----------
        pattern:
            Regular expression that dictates if the handler should be called.
        handler:
            The handler itself
        """
        self.completion_handlers[pattern] = handler

    def reset_diagnostics(self):
        """Reset the list of diagnostics."""
        self.diagnostics = {filepath: [] for filepath in self.diagnostics.keys()}

    def write(self, line):
        """This method lets us catch output from Sphinx."""

        match = PROBLEM_PATTERN.match(line)
        if match:
            filepath = match.group("file")
            severity = PROBLEM_SEVERITY.get(
                match.group("type"), PROBLEM_SEVERITY["ERROR"]
            )
            diagnostics = self.diagnostics.get(filepath, None)

            if diagnostics is None:
                diagnostics = []

            try:
                line_number = int(match.group("line"))
            except ValueError as exc:
                self.logger.error("Unable to parse line number", exc)
                line_number = 1

            range_ = Range(Position(line_number - 1, 0), Position(line_number, 0))
            diagnostics.append(
                Diagnostic(
                    range_, match.group("message"), severity=severity, source="sphinx"
                )
            )

            self.diagnostics[filepath] = diagnostics

        self.sphinx_log.info(line)


def initalize_sphinx(rst: RstLanguageServer):
    """Initialize a Sphinx application instance for the current workspace."""
    rst.logger.debug("Workspace root %s", rst.workspace.root_uri)

    root = pathlib.Path(rst.workspace.root_uri.replace("file://", ""))
    candidates = list(root.glob("**/conf.py"))

    if len(candidates) == 0:
        rst.show_message(
            'Unable to find your project\'s "conf.py", features wil be limited',
            msg_type=MessageType.Warning,
        )
        return

    src = candidates[0].parent
    # TODO: Create a unique scratch space based on the project.
    build = appdirs.user_cache_dir("esbonio", "swyddfa")
    doctrees = pathlib.Path(build) / "doctrees"

    rst.logger.debug("Config dir %s", src)
    rst.logger.debug("Src dir %s", src)
    rst.logger.debug("Build dir %s", build)
    rst.logger.debug("Doctree dir %s", str(doctrees))

    # Disable color escape codes in Sphinx's log messages
    console.nocolor()

    try:
        rst.app = Sphinx(src, src, build, doctrees, "html", status=rst, warning=rst)
    except Exception as exc:
        rst.sphinx_log.error(exc)
        rst.show_message(
            "There was an error initializing Sphinx, see output window for details.",
            msg_type=MessageType.Error,
        )


server = RstLanguageServer()
builtin_modules = ["esbonio.lsp.completion.directives", "esbonio.lsp.completion.roles"]


@server.feature(INITIALIZED)
def on_initialized(rst: RstLanguageServer, params: InitializeParams):

    initalize_sphinx(rst)

    # TODO: Handle failures.
    for mod in builtin_modules:
        module = importlib.import_module(mod)
        init = getattr(module, "init")
        init(rst)

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
        rst.logger.debug("Match %s", match)
        if match:
            items += handler(rst, match, line, doc)

    return CompletionList(False, items)


@server.feature(TEXT_DOCUMENT_DID_SAVE)
def _(rst: RstLanguageServer, params: DidSaveTextDocumentParams):
    """Re-read sources on save so we get the latest completion targets."""

    # TODO: Reload everything if a modification to conf.py is made.
    #       Requires the client to be listening for changes to conf.py
    # init_sphinx(rst)

    update(rst)
    return
