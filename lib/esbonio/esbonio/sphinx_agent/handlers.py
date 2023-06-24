import logging
import os.path
import pathlib
from functools import partial
from typing import IO
from typing import Optional
from typing import Type

from sphinx import __version__ as __sphinx_version__
from sphinx.application import Sphinx
from sphinx.util import console
from sphinx.util import logging as sphinx_logging_module
from sphinx.util.logging import NAMESPACE as SPHINX_LOG_NAMESPACE
from sphinx.util.logging import VERBOSITY_MAP

from . import types
from .config import SphinxConfig
from .log import SphinxLogHandler
from .transforms import LineNumberTransform
from .util import send_error
from .util import send_message

HANDLERS = {}
STATIC_DIR = (pathlib.Path(__file__).parent / "static").resolve()

# Global state.... for now
sphinx_app: Optional[Sphinx] = None
sphinx_log: Optional[SphinxLogHandler] = None


def handler(t: Type):
    def wrapper(f):
        HANDLERS[t.method] = (t, f)
        return f

    return wrapper


@handler(types.CreateApplicationRequest)
def create_sphinx_app(request: types.CreateApplicationRequest):
    """Create a new sphinx application instance."""
    sphinx_config = SphinxConfig.fromcli(request.params.command)
    if sphinx_config is None:
        raise ValueError("Invalid build command")

    sphinx_args = sphinx_config.to_application_args()

    # Override Sphinx's logging setup with our own.
    sphinx_logging_module.setup = partial(logging_setup, sphinx_config)
    global sphinx_app
    sphinx_app = Sphinx(**sphinx_args)

    if request.params.enable_sync_scrolling:
        # Push our folder of static assets into the user's project.
        # Path needs to be relative to their project's confdir.
        reldir = os.path.relpath(str(STATIC_DIR), start=sphinx_app.confdir)
        sphinx_app.config.html_static_path.append(reldir)

        sphinx_app.add_js_file("webview.js")

        # Inject source line numbers into build output
        sphinx_app.add_transform(LineNumberTransform)

    response = types.CreateApplicationResponse(
        id=request.id,
        result=types.SphinxInfo(
            version=__sphinx_version__,
            conf_dir=sphinx_app.confdir,
            build_dir=sphinx_app.outdir,
            builder_name=sphinx_app.builder.name,
            src_dir=sphinx_app.srcdir,
        ),
        jsonrpc=request.jsonrpc,
    )
    send_message(response)


@handler(types.BuildRequest)
def build_sphinx_app(request: types.BuildRequest):
    """Trigger a Sphinx build."""

    if sphinx_app is None:
        send_error(id=request.id, code=-32803, message="Sphinx app not initialzied")
        return

    try:
        sphinx_app.build()
        response = types.BuildResponse(
            id=request.id,
            result=types.BuildResult(),
            jsonrpc=request.jsonrpc,
        )
        send_message(response)
    except Exception:
        send_error(id=request.id, code=-32602, message="Sphinx build failed.")


def logging_setup(config: SphinxConfig, app: Sphinx, status: IO, warning: IO):
    """Setup Sphinx's logging so that it integrates well with the parent language
    server."""

    # Disable color escape codes in Sphinx's log messages
    console.nocolor()

    if not config.silent:
        sphinx_logger = logging.getLogger(SPHINX_LOG_NAMESPACE)

        # Be sure to remove any old handlers
        for handler in sphinx_logger.handlers:
            if isinstance(handler, SphinxLogHandler):
                sphinx_logger.handlers.remove(handler)
                sphinx_log = None

        sphinx_log = SphinxLogHandler(app)
        sphinx_logger.addHandler(sphinx_log)

        if config.quiet:
            level = logging.WARNING
        else:
            level = VERBOSITY_MAP[app.verbosity]

        sphinx_logger.setLevel(level)
        sphinx_log.setLevel(level)

        formatter = logging.Formatter("%(message)s")
        sphinx_log.setFormatter(formatter)
