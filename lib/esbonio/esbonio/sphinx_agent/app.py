from __future__ import annotations

import logging
import pathlib
from typing import IO

from sphinx.application import Sphinx as _Sphinx
from sphinx.util import console
from sphinx.util import logging as sphinx_logging_module
from sphinx.util.logging import NAMESPACE as SPHINX_LOG_NAMESPACE

from .database import Database
from .log import DiagnosticFilter

sphinx_logger = logging.getLogger(SPHINX_LOG_NAMESPACE)
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

        # Override sphinx's usual logging setup function
        sphinx_logging_module.setup = setup_logging  # type: ignore


class Sphinx(_Sphinx):
    """A regular sphinx application with a few extra fields."""

    esbonio: Esbonio

    def __init__(self, *args, **kwargs):
        # Disable color codes
        console.nocolor()

        self.esbonio = Esbonio(
            dbpath=pathlib.Path(kwargs["outdir"], "esbonio.db").resolve(),
            app=self,
        )

        super().__init__(*args, **kwargs)
