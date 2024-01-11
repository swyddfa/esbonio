import inspect
import logging
import os.path
import pathlib
import sys
import traceback
import typing
from functools import partial
from typing import IO
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Type
from uuid import uuid4

import sphinx.application
from sphinx import __version__ as __sphinx_version__
from sphinx.util import console
from sphinx.util import logging as sphinx_logging_module
from sphinx.util.logging import NAMESPACE as SPHINX_LOG_NAMESPACE
from sphinx.util.logging import VERBOSITY_MAP

from .. import types
from ..app import Sphinx
from ..config import SphinxConfig
from ..log import SphinxLogHandler
from ..transforms import LineNumberTransform
from ..util import send_error
from ..util import send_message

STATIC_DIR = (pathlib.Path(__file__).parent.parent / "static").resolve()
sphinx_logger = logging.getLogger(SPHINX_LOG_NAMESPACE)

# Inject our own 'core' extensions into Sphinx
sphinx.application.builtin_extensions += (
    f"{__name__}.files",
    f"{__name__}.diagnostics",
    f"{__name__}.symbols",
    f"{__name__}.directives",
)


class SphinxHandler:
    """Responsible for implementing the JSON-RPC API exposed by the Sphinx agent."""

    def __init__(self):
        self.app: Optional[Sphinx] = None
        """The sphinx application instance"""

        self._content_overrides: Dict[pathlib.Path, str] = {}
        """Holds any additional content to inject into a build."""

        self._handlers: Dict[str, Tuple[Type, Callable]] = self._register_handlers()

    def get(self, method: str) -> Optional[Tuple[Type, Callable]]:
        """Return the handler for the given method - if possible.

        Parameters
        ----------
        method
           The name of the method

        Returns
        -------
        Optional[Tuple[Type, Callable]]
           A tuple where the first element is the type definition
           representing the message body, the second element is the method which
           implements it.

           If ``None``, the given method is unknown.

        """
        return self._handlers.get(method)

    def _register_handlers(self) -> Dict[str, Tuple[Type, Callable]]:
        """Return a map of all the handlers we provide.

        A handler

        - must be a method on this class
        - the must take a single parameter called ``request``
        - the type annotation for that parameter must correspond with a ``XXXRequest``
          class definition from the ``types`` module.

        Returns
        -------
        Dict[str, Tuple[Type, Callable]]
           A dictonary where the keys are the method names implemented by this class.
           Values are a tuple where the first element is the type definition
           representing the message body, the second element is the method which
           implements it.
        """
        handlers: Dict[str, Tuple[Type, Callable]] = {}

        for name in dir(self):
            method_func = getattr(self, name)
            if name.startswith("_") or not inspect.ismethod(method_func):
                continue

            parameters = inspect.signature(method_func).parameters
            if set(parameters.keys()) != {"request"}:
                continue

            request_type = typing.get_type_hints(method_func)["request"]
            if not all(
                [hasattr(request_type, "jsonrpc"), hasattr(request_type, "method")]
            ):
                continue

            handlers[request_type.method] = (request_type, method_func)

        return handlers

    def create_sphinx_app(self, request: types.CreateApplicationRequest):
        """Create a new sphinx application instance."""
        sphinx_config = SphinxConfig.fromcli(request.params.command)
        if sphinx_config is None:
            raise ValueError("Invalid build command")

        sphinx_args = sphinx_config.to_application_args()

        # Override Sphinx's logging setup with our own.
        sphinx_logging_module.setup = partial(self.setup_logging, sphinx_config)
        self.app = Sphinx(**sphinx_args)

        # Connect event handlers.
        self.app.connect("env-before-read-docs", self._cb_env_before_read_docs)
        self.app.connect("source-read", self._cb_source_read, priority=0)

        # TODO: Sphinx 7.x has introduced a `include-read` event
        # See: https://github.com/sphinx-doc/sphinx/pull/11657

        if request.params.enable_sync_scrolling:
            _enable_sync_scrolling(self.app)

        response = types.CreateApplicationResponse(
            id=request.id,
            result=types.SphinxInfo(
                id=str(uuid4()),
                version=__sphinx_version__,
                conf_dir=str(self.app.confdir),
                build_dir=str(self.app.outdir),
                builder_name=self.app.builder.name,
                src_dir=str(self.app.srcdir),
                dbpath=str(self.app.esbonio.db.path),
            ),
            jsonrpc=request.jsonrpc,
        )
        send_message(response)

    def _cb_env_before_read_docs(self, app: Sphinx, env, docnames: List[str]):
        """Used to add additional documents to the "to build" list."""

        is_building = set(docnames)

        for docname in env.found_docs - is_building:
            filepath = pathlib.Path(env.doc2path(docname, base=True))
            if filepath in self._content_overrides:
                docnames.append(docname)

    def _cb_source_read(self, app: Sphinx, docname: str, source):
        """Called whenever sphinx reads a file from disk."""

        filepath = app.env.doc2path(docname, base=True)

        # Override file contents if necessary
        path = pathlib.Path(filepath)
        if (content := self._content_overrides.get(path)) is not None:
            source[0] = content

    def setup_logging(self, config: SphinxConfig, app: Sphinx, status: IO, warning: IO):
        """Setup Sphinx's logging so that it integrates well with the parent language
        server."""

        # Disable color escape codes in Sphinx's log messages
        console.nocolor()

        if not config.silent:
            # Be sure to remove any old handlers
            for handler in sphinx_logger.handlers:
                if isinstance(handler, SphinxLogHandler):
                    sphinx_logger.handlers.remove(handler)
                    self.log_handler = None

            app.esbonio.log = SphinxLogHandler(app)
            sphinx_logger.addHandler(app.esbonio.log)

            if config.quiet:
                level = logging.WARNING
            else:
                level = VERBOSITY_MAP[app.verbosity]

            sphinx_logger.setLevel(level)
            app.esbonio.log.setLevel(level)

            formatter = logging.Formatter("%(message)s")
            app.esbonio.log.setFormatter(formatter)

    def build_sphinx_app(self, request: types.BuildRequest):
        """Trigger a Sphinx build."""

        if self.app is None:
            send_error(id=request.id, code=-32803, message="Sphinx app not initialized")
            return

        self._content_overrides = {
            pathlib.Path(p): content
            for p, content in request.params.content_overrides.items()
        }

        try:
            self.app.build()

            response = types.BuildResponse(
                id=request.id,
                result=types.BuildResult(),
                jsonrpc=request.jsonrpc,
            )
            send_message(response)
        except Exception as exc:
            message = "".join(traceback.format_exception_only(type(exc), exc))
            sphinx_logger.error("sphinx-build failed", exc_info=True)
            send_error(
                id=request.id, code=-32603, message=f"sphinx-build failed: {message}"
            )

    def notify_exit(self, request: types.ExitNotification):
        """Sent from the client to signal that the agent should exit."""
        sys.exit(0)


def _enable_sync_scrolling(app: Sphinx):
    """Given a Sphinx application, configure it so that we can support syncronised
    scrolling."""

    # On OSes like Fedora Silverblue where `/home` is a symlink for `/var/home`
    # we could have a situation where `STATIC_DIR` and `app.confdir` have
    # different root dirs... which is enough to cause `os.path.relpath` to return
    # the wrong path.
    #
    # Fully resolving both `STATIC_DIR` and `app.confdir` should be enough to
    # mitigate this.
    confdir = pathlib.Path(app.confdir).resolve()

    # Push our folder of static assets into the user's project.
    # Path needs to be relative to their project's confdir.
    reldir = os.path.relpath(str(STATIC_DIR), start=str(confdir))
    app.config.html_static_path.append(reldir)

    app.add_js_file("webview.js")

    # Inject source line numbers into build output
    app.add_transform(LineNumberTransform)
