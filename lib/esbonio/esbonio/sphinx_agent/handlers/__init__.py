import inspect
import logging
import sys
import traceback
import typing
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Type

import sphinx.application
from sphinx import __version__ as __sphinx_version__
from sphinx.util.logging import NAMESPACE as SPHINX_LOG_NAMESPACE

from .. import types
from ..app import Sphinx
from ..config import SphinxConfig
from ..types import Uri
from ..util import send_error
from ..util import send_message

sphinx_logger = logging.getLogger(SPHINX_LOG_NAMESPACE)

# Inject our own 'core' extensions into Sphinx
sphinx.application.builtin_extensions += (
    f"{__name__}.webview",
    f"{__name__}.files",
    f"{__name__}.diagnostics",
    f"{__name__}.symbols",
    f"{__name__}.directives",
    f"{__name__}.roles",
    f"{__name__}.domains",
)


class SphinxHandler:
    """Responsible for implementing the JSON-RPC API exposed by the Sphinx agent."""

    def __init__(self):
        self.app: Optional[Sphinx] = None
        """The sphinx application instance"""

        self._content_overrides: Dict[Uri, str] = {}
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
        self.app = Sphinx(**sphinx_args)

        # Connect event handlers.
        # TODO: Sphinx 7.x has introduced a `include-read` event
        # See: https://github.com/sphinx-doc/sphinx/pull/11657
        self.app.connect("env-before-read-docs", self._cb_env_before_read_docs)
        self.app.connect("source-read", self._cb_source_read, priority=0)

        response = types.CreateApplicationResponse(
            id=request.id,
            result=types.SphinxInfo(
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
            uri = Uri.for_file(env.doc2path(docname, base=True))
            if uri in self._content_overrides:
                docnames.append(docname)

    def _cb_source_read(self, app: Sphinx, docname: str, source):
        """Called whenever sphinx reads a file from disk."""

        uri = Uri.for_file(app.env.doc2path(docname, base=True))
        if (content := self._content_overrides.get(uri, None)) is not None:
            source[0] = content

    def build_sphinx_app(self, request: types.BuildRequest):
        """Trigger a Sphinx build."""

        if self.app is None:
            send_error(id=request.id, code=-32803, message="Sphinx app not initialized")
            return

        self._content_overrides = {
            Uri.parse(p): content
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

        finally:
            self.app._warncount = 0

    def notify_exit(self, request: types.ExitNotification):
        """Sent from the client to signal that the agent should exit."""
        sys.exit(0)
