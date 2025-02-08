from __future__ import annotations

import ast
import logging
import pathlib
import sys
import typing

from sphinx.application import Sphinx as _Sphinx
from sphinx.errors import ThemeError
from sphinx.util import console
from sphinx.util import logging as sphinx_logging_module
from sphinx.util.logging import NAMESPACE as SPHINX_LOG_NAMESPACE

from . import types
from .database import Database
from .log import DiagnosticFilter

if typing.TYPE_CHECKING:
    from typing import IO
    from typing import Any
    from typing import Literal

    from docutils.nodes import Element
    from docutils.parsers.rst import Directive

    DirectiveDefinition = tuple[
        str, type[Directive], list[types.Directive.ArgumentProvider]
    ]
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
        self.app: _Sphinx = app
        self.db = Database(dbpath)
        self.log = DiagnosticFilter(app)

        self._roles: list[RoleDefinition] = []
        """Roles captured during Sphinx startup."""

        self._directives: list[DirectiveDefinition] = []
        """Directives captured during Sphinx startup."""

        self._config_ast: ast.Module | Literal[False] | None = None
        """The parsed AST of the user's conf.py file.
        If ``False``, we already tried parsing the module and were unable to."""

        self.diagnostics: dict[types.Uri, set[types.Diagnostic]] = {}
        """Recorded diagnostics."""

    @property
    def config_uri(self) -> types.Uri:
        return types.Uri.for_file(pathlib.Path(self.app.confdir, "conf.py"))

    @property
    def config_ast(self) -> ast.Module | None:
        """Return the AST for the user's conf.py (if possible)"""

        if self._config_ast is not None:
            return self._config_ast or None  # convert ``False`` to ``None``

        try:
            conf_py = pathlib.Path(self.app.confdir, "conf.py")
            self._config_ast = ast.parse(source=conf_py.read_text())
            return self._config_ast
        except Exception as exc:
            logger.debug("Unable to parse user's conf.py: %s", exc)
            self._config_ast = False

            return None

    def add_directive(
        self,
        name: str,
        directive: type[Directive],
        argument_providers: list[types.Directive.ArgumentProvider] | None = None,
    ):
        """Register a directive with esbonio.

        Parameters
        ----------
        name
           The name of the directive, as the user would type in a document

        directive
           The directive's implementation

        argument_providers
           A list of argument providers for the role
        """
        self._directives.append((name, directive, argument_providers or []))

    @staticmethod
    def create_directive_argument_provider(
        name: str, **kwargs
    ) -> types.Directive.ArgumentProvider:
        """Create a new directive argument provider

        Parameters
        ----------
        name
           The name of the provider

        kwargs
           Additional arguments to pass to the provider instance

        Returns
        -------
        types.Directive.ArgumentProvider
           The target provider
        """
        return types.Directive.ArgumentProvider(name, kwargs)

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

        # `try_run_init` may call `__init__` more than once, this could lead to spamming
        # the user with warning messages, so we will suppress these messages if the
        # retry counter has been set.
        self._esbonio_retry_count = 0
        try_run_init(self, super().__init__, *args, **kwargs)

    def add_role(self, name: str, role: Any, override: bool = False):
        super().add_role(name, role, override or self._esbonio_retry_count > 0)
        self.esbonio.add_role(name, role)

    def add_directive(self, name: str, cls: type[Directive], override: bool = False):
        super().add_directive(name, cls, override or self._esbonio_retry_count > 0)
        self.esbonio.add_directive(name, cls)

    def add_node(self, node: type[Element], override: bool = False, **kwargs):
        super().add_node(node, override or self._esbonio_retry_count > 0, **kwargs)

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
           The name of the extension that caused the exception

        exc
           The exception instance
        """

        if (config := self.esbonio.config_ast) is None:
            return

        # Now attempt to find the soure location of the extenison.
        if (range_ := find_extension_declaration(config, extname)) is None:
            logger.debug("Unable to locate declaration of extension: %r", extname)
            return

        diagnostic = types.Diagnostic(
            range=range_, message=f"{exc}", severity=types.DiagnosticSeverity.Error
        )

        uri = self.esbonio.config_uri
        logger.debug("Adding diagnostic %s: %s", uri, diagnostic)
        self.esbonio.diagnostics.setdefault(uri, set()).add(diagnostic)


def try_run_init(app: Sphinx, init_fn, *args, **kwargs):
    """Try and run Sphinx's ``__init__`` function.

    There are occasions where Sphinx will try and throw an error that is recoverable
    e.g. a missing theme. In these situations we want to suppress the error, record a
    diagnostic, and try again - which is what this function will do.

    Some errors however, are not recoverable in which case we will allow the error to
    proceed as normal.

    Parameters
    ----------
    app
       The application instance we are trying to initialize

    init_fn
       The application's `__init__` method, as returned by ``super().__init__``

    args
       Positional arguments to ``__init__``

    retries
       Max number of retries, a fallback in case we end up creating infinite recursion

    kwargs
       Keyword arguments to ``__init__``
    """

    if app._esbonio_retry_count >= 100:
        raise RuntimeError("Unable to initialize Sphinx: max retries exceeded")

    try:
        init_fn(*args, **kwargs)
    except ThemeError as exc:
        # Fallback to the default theme.
        print(f"ThemeError: {exc}", file=sys.stderr)  # noqa: T201

        fallback_theme = "alabaster"
        kwargs.setdefault("confoverrides", {})["html_theme"] = fallback_theme
        kwargs["confoverrides"]["html_theme_options"] = {}

        app._esbonio_retry_count += 1
        report_theme_error(app, exc)

        print(f"Retrying with html_theme = {fallback_theme!r}\n", file=sys.stderr)  # noqa: T201
        try_run_init(app, init_fn, *args, **kwargs)
    except Exception:
        logger.exception("Unable to initialize Sphinx")
        raise


def report_theme_error(app: Sphinx, exc: ThemeError):
    """Attempt to convert the given theme error into a useful diagnostic.

    Parameters
    ----------
    app
       The Sphinx object being initialized

    exc
       The error instance
    """

    if (config := app.esbonio.config_ast) is None:
        return

    if (range_ := find_html_theme_declaration(config)) is None:
        return

    diagnostic = types.Diagnostic(
        range=range_,
        message=f"{exc}",
        severity=types.DiagnosticSeverity.Error,
    )

    uri = app.esbonio.config_uri
    logger.debug("Adding diagnostic %s: %s", uri, diagnostic)
    app.esbonio.diagnostics.setdefault(uri, set()).add(diagnostic)


def find_html_theme_declaration(mod: ast.Module) -> types.Range | None:
    """Attempt to find the location in the user's conf.py file where the ``html_theme``
    was declared."""

    for node in mod.body:
        if not isinstance(node, ast.Assign):
            continue

        if len(targets := node.targets) != 1:
            continue

        if not isinstance(name := targets[0], ast.Name):
            continue

        if name.id == "html_theme":
            break

    else:
        # Nothing found, abort
        logger.debug("Unable to find 'html_theme' node")
        return None

    return ast_node_to_range(node)


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

    return ast_node_to_range(element)


def ast_node_to_range(node: ast.stmt | ast.expr) -> types.Range:
    """Convert the given ast node to a range."""

    # Finally, try and extract the source location.
    start_line = node.lineno - 1
    start_char = node.col_offset

    if (end_line := (node.end_lineno or 0) - 1) < 0:
        end_line = start_line + 1
        end_char: int | None = 0

    elif (end_char := node.end_col_offset) is None:
        end_line += 1
        end_char = 0

    return types.Range(
        start=types.Position(line=start_line, character=start_char),
        end=types.Position(line=end_line, character=end_char or 0),
    )
