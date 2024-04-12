from __future__ import annotations

import pathlib

from sphinx.application import Sphinx as _Sphinx
from sphinx.util import console

from .database import Database
from .log import DiagnosticFilter


class Esbonio:
    """Esbonio specific functionality."""

    db: Database

    log: DiagnosticFilter

    def __init__(self, dbpath: pathlib.Path, app: _Sphinx):
        self.db = Database(dbpath)
        self.log = DiagnosticFilter(app)


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
