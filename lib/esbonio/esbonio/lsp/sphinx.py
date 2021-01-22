"""Code for managing sphinx applications."""
import logging
import pathlib
import re

import appdirs

from pygls.types import (
    Diagnostic,
    DiagnosticSeverity,
    DidSaveTextDocumentParams,
    MessageType,
    Position,
    Range,
)
from sphinx.application import Sphinx
from sphinx.util import console

from esbonio.lsp import RstLanguageServer


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


class SphinxManagement:
    """A LSP Server feature that manages the Sphinx application instance for the
    project."""

    def __init__(self, rst: RstLanguageServer):
        self.rst = rst

        self.diagnostics = {}
        """A place to keep track of diagnostics we can publish to the client."""

        self.sphinx_log = logging.getLogger("esbonio.sphinx")
        """The logger that should be used by a Sphinx application"""

    def initialize(self):
        self.create_app()
        self.refresh_app()

    def save(self, params: DidSaveTextDocumentParams):
        self.refresh_app()

    def create_app(self):
        """Initialize a Sphinx application instance for the current workspace."""
        self.rst.logger.debug("Workspace root %s", self.rst.workspace.root_uri)

        root = pathlib.Path(self.rst.workspace.root_uri.replace("file://", ""))
        candidates = list(root.glob("**/conf.py"))

        if len(candidates) == 0:
            self.rst.show_message(
                'Unable to find your project\'s "conf.py", features wil be limited',
                msg_type=MessageType.Warning,
            )
            return

        src = candidates[0].parent
        # TODO: Create a unique scratch space based on the project.
        build = appdirs.user_cache_dir("esbonio", "swyddfa")
        doctrees = pathlib.Path(build) / "doctrees"

        self.rst.logger.debug("Config dir %s", src)
        self.rst.logger.debug("Src dir %s", src)
        self.rst.logger.debug("Build dir %s", build)
        self.rst.logger.debug("Doctree dir %s", str(doctrees))

        # Disable color escape codes in Sphinx's log messages
        console.nocolor()

        try:
            self.rst.app = Sphinx(
                src, src, build, doctrees, "html", status=self, warning=self
            )
        except Exception as exc:
            message = (
                "There was an error initializing Sphinx, "
                "see output window for details.",
            )

            self.rst.sphinx_log.error(exc)
            self.rst.show_message(
                message,
                msg_type=MessageType.Error,
            )

    def refresh_app(self):
        if self.rst.app is None:
            return

        self.reset_diagnostics()
        self.rst.app.builder.read()

        for doc, diagnostics in self.diagnostics.items():
            self.rst.publish_diagnostics(doc, diagnostics)

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


def setup(rst: RstLanguageServer):
    rst.logger.debug("Running setup.")
    sphinx_management = SphinxManagement(rst)
    rst.add_feature(sphinx_management)
