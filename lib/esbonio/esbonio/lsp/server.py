"""Our Lanague Server Class Definition."""
import logging
import re

from pygls.server import LanguageServer
from pygls.types import Diagnostic, DiagnosticSeverity, Position, Range

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

        self.directives = {}
        """Dictionary holding the directives that have been registered."""

        self.roles = {}
        """Dictionary holding the roles that have been registered."""

        self.targets = {}
        """Dictionary holding objects that may be referenced by a role."""

        self.target_types = {}
        """Dictionary holding role names and the object types they can reference."""

        self.diagnostics = {}
        """A place to keep track of diagnostics we can publish to the client."""

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


server = RstLanguageServer()
