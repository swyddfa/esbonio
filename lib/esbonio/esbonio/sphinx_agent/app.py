from __future__ import annotations

import ast
import logging
import pathlib
import typing

from sphinx.application import Sphinx as _Sphinx
from sphinx.util import console
from sphinx.util import logging as sphinx_logging_module
from sphinx.util.logging import NAMESPACE as SPHINX_LOG_NAMESPACE

from . import types
from .database import Database
from .log import DiagnosticFilter

if typing.TYPE_CHECKING:
    from typing import IO
    from typing import Any

    RoleDefinition = tuple[str, Any, list[types.Role.TargetProvider]]

sphinx_logger = logging.getLogger(SPHINX_LOG_NAMESPACE)
logger = sphinx_logger.getChild("esbonio")
sphinx_log_setup = sphinx_logging_module.setup


def setup_logging(app: Sphinx, status: IO, warning: IO):
    # Run the usual setup
    sphinx_log_setup(app, status, warning)

    # Attach our diagnostic filter to the warning handler.
    for handler in sphinx_logger.handlers:
        if handler.level == logging.WARNING:
            handler.addFilter(app.esbonio.log)


class Esbonio:
    """Esbonio specific functionality."""

    db: Database

    log: DiagnosticFilter

    def __init__(self, dbpath: pathlib.Path, app: _Sphinx):
        self.db = Database(dbpath)
        self.log = DiagnosticFilter(app)

        self._roles: list[RoleDefinition] = []
        """Roles captured during Sphinx startup."""


        self.diagnostics: dict[types.Uri, set[types.Diagnostic]] = {}
        """Recorded diagnostics."""
    def add_role(
        self,
        name: str,
        role: Any,
        target_providers: list[types.Role.TargetProvider] | None = None,
    ):
        """Register a role with esbonio.

        Parameters
        ----------
        name
           The name of the role, as the user would type in a document

        role
           The role's implementation

        target_providers
           A list of target providers for the role
        """
        self._roles.append((name, role, target_providers or []))

    @staticmethod
    def create_role_target_provider(name: str, **kwargs) -> types.Role.TargetProvider:
        """Create a new role target provider

        Parameters
        ----------
        name
           The name of the provider

        kwargs
           Additional arguments to pass to the provider instance

        Returns
        -------
        types.Role.TargetProvider
           The target provider
        """
        return types.Role.TargetProvider(name, kwargs)


class Sphinx(_Sphinx):
    """An extended sphinx application that integrates with esbonio."""

    esbonio: Esbonio

    def __init__(self, *args, **kwargs):
        # Disable color codes
        console.nocolor()

        # Add in esbonio specific functionality
        self.esbonio = Esbonio(
            dbpath=pathlib.Path(kwargs["outdir"], "esbonio.db").resolve(),
            app=self,
        )

        # Override sphinx's usual logging setup function
        sphinx_logging_module.setup = setup_logging  # type: ignore

        super().__init__(*args, **kwargs)

    def add_role(self, name: str, role: Any, override: bool = False):
        super().add_role(name, role, override)
        self.esbonio.add_role(name, role)

    def setup_extension(self, extname: str):
        """Override Sphinx's implementation of `setup_extension`

        This implementation
        - Will suppress errors caused by missing extensions
        - Attempt to report errors where possible, as diagnostics
        """
        try:
            super().setup_extension(extname)
        except Exception as exc:
            # Attempt to produce useful diagnostics.
            self._report_missing_extension(extname, exc)

    def _report_missing_extension(self, extname: str, exc: Exception):
        """Check to see if the given exception corresponds to a missing extension.

        If so, attempt to produce a diagnostic to highlight this to the user.

        Parameters
        ----------
        extname
           The name of the extension that caused the excetion

        exc
           The exception instance
        """

        if not isinstance(cause := exc.__cause__, ImportError):
            return

        # Parse the user's config file
        # TODO: Move this somewhere more central.
        try:
            conf_py = pathlib.Path(self.confdir, "conf.py")
            config = ast.parse(source=conf_py.read_text())
        except Exception:
            logger.debug("Unable to parse user's conf.py")
            return

        # Now attempt to find the soure location of the extenison.
        if (range_ := find_extension_declaration(config, extname)) is None:
            logger.debug("Unable to locate declaration of extension: %r", extname)
            return

        diagnostic = types.Diagnostic(
            range=range_, message=str(cause), severity=types.DiagnosticSeverity.Error
        )

        uri = types.Uri.for_file(conf_py)
        logger.debug("Adding diagnostic %s: %s", uri, diagnostic)
        self.esbonio.diagnostics.setdefault(uri, set()).add(diagnostic)


def find_extension_declaration(mod: ast.Module, extname: str) -> types.Range | None:
    """Attempt to find the location in the user's conf.py file where the given
    ``extname`` was declared.

    This function will never be perfect (conf.py is after all, turing complete!).
    However, it *should* be possible to write something that can handle most cases.
    """

    # First try and locate the node corresponding to `extensions = [ ... ]`
    for node in mod.body:
        if not isinstance(node, ast.Assign):
            continue

        if len(targets := node.targets) != 1:
            continue

        if not isinstance(name := targets[0], ast.Name):
            continue

        if name.id == "extensions":
            break

    else:
        # Nothing found, abort
        logger.debug("Unable to find 'extensions' node")
        return None

    # Now try to find the node corresponding to `'extname'`
    if not isinstance(extlist := node.value, ast.List):
        return None

    for element in extlist.elts:
        if not isinstance(element, ast.Constant):
            continue

        if element.value == extname:
            break
    else:
        # Nothing found, abort
        logger.debug("Unable to find node for extension %r", extname)
        return None

    # Finally, try and extract the source location.
    start_line = element.lineno - 1
    start_char = element.col_offset

    if (end_line := (element.end_lineno or 0) - 1) < 0:
        end_line = start_line + 1
        end_char: int | None = 0

    elif (end_char := element.end_col_offset) is None:
        end_line += 1
        end_char = 0

    return types.Range(
        start=types.Position(line=start_line, character=start_char),
        end=types.Position(line=end_line, character=end_char or 0),
    )
