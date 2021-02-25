"""Code for managing sphinx applications."""
import collections
import hashlib
import logging
import pathlib
import re

from typing import Iterator, Optional, Tuple
from urllib.parse import urlparse, unquote

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
from sphinx.domains import Domain
from sphinx.util import console

from esbonio.lsp import LanguageFeature, RstLanguageServer


PROBLEM_PATTERN = re.compile(
    r"""
    (?P<file>(.*:\\)?[^:]*):   # Capture the path to the file containing the problem
    ((?P<line>\d+):)?          # Some errors may specify a line number.
    \s(?P<type>[^:]*):         # Capture the type of error
    (\s+)?(?P<message>.*)      # Capture the error message
    """,
    re.VERBOSE,
)
"""Regular Expression used to identify warnings/errors in Sphinx's output.

For example::

   /path/to/file.rst: WARNING: document isn't included in any toctree
   /path/to/file.rst:4: WARNING: toctree contains reference to nonexisting document 'changelog',

"""


PROBLEM_SEVERITY = {
    "WARNING": DiagnosticSeverity.Warning,
    "ERROR": DiagnosticSeverity.Error,
}


def get_filepath(uri: str) -> pathlib.Path:
    """Given a uri, return the filepath component."""

    uri = urlparse(uri)
    return pathlib.Path(unquote(uri.path))


def get_domains(app: Sphinx) -> Iterator[Tuple[str, Domain]]:
    """Get all the domains registered with an applications.

    Returns a generator that iterates through all of an application's domains,
    taking into account configuration variables such as ``primary_domain``.
    Yielded values will be a tuple of the form ``(prefix, domain)`` where

    - ``prefix`` is the namespace that should be used when referencing items
      in the domain
    - ``domain`` is the domain object itself.
    """

    if app is None:
        return []

    domains = app.env.domains
    primary_domain = app.config.primary_domain

    for name, domain in domains.items():
        prefix = name

        # Items from the standard and primary domains don't require the namespace prefix
        if name == "std" or name == primary_domain:
            prefix = ""

        yield prefix, domain


def find_conf_py(root_uri: str) -> Optional[pathlib.Path]:
    """Attempt to find Sphinx's configuration file in the given workspace."""

    root = get_filepath(root_uri)

    # Strangely for windows paths, there's an extra leading slash which we have to
    # remove ourselves.
    if isinstance(root, pathlib.WindowsPath) and str(root).startswith("\\"):
        root = pathlib.Path(str(root)[1:])

    # Try and find Sphinx's conf.py file
    ignore_paths = [".tox", "site-packages"]

    for candidate in root.glob("**/conf.py"):

        # Skip files that obviously aren't part of the project
        if any(path in str(candidate) for path in ignore_paths):
            continue

        return candidate


class DiagnosticList(collections.UserList):
    """A list type dedicated to holding diagnostics.

    This is mainly to ensure that only one instance of a diagnostic ever gets
    reported.
    """

    def append(self, item: Diagnostic):

        if not isinstance(item, Diagnostic):
            raise TypeError("Expected Diagnostic")

        for existing in self.data:
            fields = [
                existing.range == item.range,
                existing.message == item.message,
                existing.severity == item.severity,
                existing.code == item.code,
                existing.source == item.source,
            ]

            if all(fields):
                # Item already added, nothing to do.
                return

        self.data.append(item)


class SphinxManagement(LanguageFeature):
    """A LSP Server feature that manages the Sphinx application instance for the
    project."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.diagnostics = {}
        """A place to keep track of diagnostics we can publish to the client."""

        self.sphinx_log = logging.getLogger("esbonio.sphinx")
        """The logger that should be used by a Sphinx application"""

    def initialize(self):
        self.create_app()

        if self.rst.app is not None:
            self.rst.app.build()

    def initialized(self):
        self.report_diagnostics()

    def save(self, params: DidSaveTextDocumentParams):

        if self.rst.app is None:
            return

        filepath = get_filepath(params.textDocument.uri)

        self.reset_diagnostics(str(filepath))
        self.rst.app.build()
        self.report_diagnostics()

    def create_app(self):
        """Initialize a Sphinx application instance for the current workspace."""
        self.rst.logger.debug("Workspace root %s", self.rst.workspace.root_uri)

        conf_py = find_conf_py(self.rst.workspace.root_uri)

        if conf_py is None:
            self.rst.show_message(
                'Unable to find your project\'s "conf.py", features wil be limited',
                msg_type=MessageType.Warning,
            )
            return

        src = conf_py.parent

        if self.rst.cache_dir is not None:
            build = self.rst.cache_dir
        else:
            # Try to pick a sensible dir based on the project's location
            cache = appdirs.user_cache_dir("esbonio", "swyddfa")
            project = hashlib.md5(str(src).encode()).hexdigest()
            build = pathlib.Path(cache) / project

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

    def report_diagnostics(self):
        """Publish the current set of diagnostics to the client."""

        for doc, diagnostics in self.diagnostics.items():

            if not doc.startswith("/"):
                doc = "/" + doc

            uri = f"file://{doc}"
            self.rst.publish_diagnostics(uri, diagnostics.data)

    def reset_diagnostics(self, filepath: str):
        """Reset the list of diagnostics for the given file.

        Parameters
        ----------
        filepath:
           The filepath that the diagnostics should be reset for.
        """
        self.diagnostics[filepath] = DiagnosticList()

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
                diagnostics = DiagnosticList()

            try:
                line_number = int(match.group("line"))
            except (TypeError, ValueError) as exc:
                self.logger.debug(
                    "Unable to parse line number: '%s'", match.group("line")
                )
                self.logger.debug(exc)

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
