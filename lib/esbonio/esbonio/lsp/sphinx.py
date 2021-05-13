"""Code for managing sphinx applications."""
import collections
import hashlib
import logging
import pathlib
import re

from typing import Iterator, Optional, Tuple
from urllib.parse import quote

import appdirs

from pygls.lsp.types import (
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

import esbonio.lsp as lsp


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


def expand_conf_dir(root_dir: str, conf_dir: str) -> str:
    """Expand the user provided conf_dir into a real path.

    Here is where we handle "variables" that can be included in the path, currently
    we support

    - ``${workspaceRoot}`` which expands to the workspace root as provided by the
      language client.

    Parameters
    ----------
    root_dir:
       The workspace root path
    conf_dir:
       The user provided path
    """

    match = re.match(r"^\${(\w+)}/.*", conf_dir)
    if not match or match.group(1) != "workspaceRoot":
        return conf_dir

    conf = pathlib.Path(conf_dir).parts[1:]
    return pathlib.Path(root_dir, *conf).resolve()


def get_src_dir(
    root_uri: str, conf_dir: pathlib.Path, config: lsp.SphinxConfig
) -> pathlib.Path:
    """Get the src dir to use based on the given config.

    By default the src dir will be the same as the conf dir, but this can
    be overriden in the given config.

    There are a number of "variables" that can be included in the path, currently
    we support

    - ``${workspaceRoot}`` which expands to the workspace root as provided by the
      language client.
    - ``${confDir}`` which expands to the configured config dir.

    Parameters
    ----------
    root_uri:
       The workspace root uri
    conf_dir:
       The project's conf dir
    config:
       The user's configuration.
    """

    if not config.src_dir:
        return conf_dir

    src_dir = config.src_dir
    root_dir = lsp.filepath_from_uri(root_uri)

    match = re.match(r"^\${(\w+)}/.*", src_dir)
    if match and match.group(1) == "workspaceRoot":
        src = pathlib.Path(src_dir).parts[1:]
        return pathlib.Path(root_dir, *src).resolve()

    if match and match.group(1) == "confDir":
        src = pathlib.Path(src_dir).parts[1:]
        return pathlib.Path(conf_dir, *src).resolve()

    return src_dir


def find_conf_dir(root_uri: str, config: lsp.SphinxConfig) -> Optional[pathlib.Path]:
    """Attempt to find Sphinx's configuration file in the given workspace."""

    root = lsp.filepath_from_uri(root_uri)

    if config.conf_dir:
        return expand_conf_dir(root, config.conf_dir)

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

        return candidate.parent


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


class SphinxManagement(lsp.LanguageFeature):
    """A LSP Server feature that manages the Sphinx application instance for the
    project."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.diagnostics = {}
        """A place to keep track of diagnostics we can publish to the client."""

        self.config: Optional[lsp.SphinxConfig] = None
        """The client's ``esbonio.sphinx.*`` configuration."""

        self._conf_dir = None
        """The directory containing Sphinx's ``conf.py``.

        The source of truth for this value should be the Sphinx application itself,
        **you should not depend on this value**.

        The only use case for this field is when a user's config is broken and there
        currently isn't a valid application object, we use this field to determine when
        a user has edited their ``conf.py`` and we should try to restart the server.
        """

        self.sphinx_log = logging.getLogger("esbonio.sphinx")
        """The logger that should be used by a Sphinx application"""

    def initialized(self, config: lsp.SphinxConfig):

        self.config = config
        self.logger.debug("%s", self.config)
        self.create_app(self.config)
        self.build_app()

    def save(self, params: DidSaveTextDocumentParams):

        filepath = lsp.filepath_from_uri(params.text_document.uri)

        # There may not be an application instance - the user's config could
        # be broken...
        if not self.rst.app:

            # ...did thry try to fix it?
            if self._conf_dir and filepath == (self._conf_dir / "conf.py"):
                self.create_app(self.config)

        # The user has updated their conf.py, we need to recreate the application.
        elif filepath == pathlib.Path(self.rst.app.confdir) / "conf.py":
            self.create_app(self.config)

        else:
            self.reset_diagnostics(str(filepath))

        self.build_app()

    def create_app(self, config: lsp.SphinxConfig):
        """Initialize a Sphinx application instance for the current workspace."""
        self.rst.logger.debug("Workspace root %s", self.rst.workspace.root_uri)

        self.diagnostics = {}
        conf_dir = find_conf_dir(self.rst.workspace.root_uri, config)

        if conf_dir is None:
            self.rst.show_message(
                'Unable to find your project\'s "conf.py", features that depend on '
                + "Sphinx will be unavailable",
                msg_type=MessageType.Warning,
            )
            return

        if self.rst.cache_dir is not None:
            build_dir = self.rst.cache_dir
        else:
            # Try to pick a sensible dir based on the project's location
            cache = appdirs.user_cache_dir("esbonio", "swyddfa")
            project = hashlib.md5(str(conf_dir).encode()).hexdigest()
            build_dir = pathlib.Path(cache) / project

        src_dir = get_src_dir(self.rst.workspace.root_uri, conf_dir, config)
        doctree_dir = pathlib.Path(build_dir) / "doctrees"

        self.rst.logger.debug("Config dir %s", conf_dir)
        self.rst.logger.debug("Src dir %s", src_dir)
        self.rst.logger.debug("Build dir %s", build_dir)
        self.rst.logger.debug("Doctree dir %s", str(doctree_dir))

        # Disable color escape codes in Sphinx's log messages
        console.nocolor()

        try:
            self.rst.app = Sphinx(
                srcdir=src_dir,
                confdir=conf_dir,
                outdir=build_dir,
                doctreedir=doctree_dir,
                buildername="html",
                status=self,
                warning=self,
            )
        except Exception as exc:
            message = "Unable to initialize Sphinx, see output window for details."
            self._conf_dir = conf_dir

            self.sphinx_log.error(exc)
            self.rst.show_message(
                message=message,
                msg_type=MessageType.Error,
            )

    def build_app(self):

        if not self.rst.app:
            return

        try:
            self.rst.app.build()
        except Exception as exc:
            message = "Unable to build documentation, see output window for details."

            self.sphinx_log.error(exc)
            self.rst.show_message(
                message=message,
                msg_type=MessageType.Error,
            )

        self.report_diagnostics()

    def report_diagnostics(self):
        """Publish the current set of diagnostics to the client."""

        for doc, diagnostics in self.diagnostics.items():

            if not doc.startswith("/"):
                doc = "/" + doc.replace("\\", "/")

            uri = f"file://{quote(doc)}"
            self.logger.debug("Publishing diagnostics for document: %s", uri)
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
                    "Unable to parse line number: '%s' - %s", match.group("line"), exc
                )

                line_number = 1

            range_ = Range(
                start=Position(line=line_number - 1, character=0),
                end=Position(line=line_number, character=0),
            )
            diagnostics.append(
                Diagnostic(
                    range=range_,
                    message=match.group("message"),
                    severity=severity,
                    source="sphinx",
                )
            )

            self.diagnostics[filepath] = diagnostics

        self.sphinx_log.info(line)


def setup(rst: lsp.RstLanguageServer):
    sphinx_management = SphinxManagement(rst)
    rst.add_feature(sphinx_management)
