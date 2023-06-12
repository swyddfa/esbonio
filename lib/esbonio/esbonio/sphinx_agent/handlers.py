import logging
from functools import partial
from typing import IO
from typing import Optional
from typing import Type

from sphinx.application import Sphinx
from sphinx.util import console
from sphinx.util import logging as sphinx_logging_module
from sphinx.util.logging import NAMESPACE as SPHINX_LOG_NAMESPACE
from sphinx.util.logging import VERBOSITY_MAP

from .config import SphinxConfig
from .log import SphinxLogHandler
from .types import CreateApplicationRequest

HANDLERS = {}

# Global state.... for now
sphinx_app: Optional[Sphinx] = None
sphinx_log: Optional[SphinxLogHandler] = None


def handler(t: Type):
    def wrapper(f):
        HANDLERS[t.method] = (t, f)
        return f

    return wrapper


@handler(CreateApplicationRequest)
def create_sphinx_app(request: CreateApplicationRequest):
    sphinx_config = SphinxConfig.fromcli(request.params.command)
    if sphinx_config is None:
        raise ValueError("Invalid build command")

    sphinx_args = sphinx_config.to_application_args()

    # Override Sphinx's logging setup with our own.
    sphinx_logging_module.setup = partial(logging_setup, sphinx_config)

    app = Sphinx(**sphinx_args)
    app.build()


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
