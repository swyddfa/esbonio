from __future__ import annotations

import pathlib
import typing

from sphinx.application import Sphinx as _Sphinx

from .database import Database
from .log import SphinxLogHandler


class Esbonio:
    """Esbonio specific functionality."""

    db: Database

    log: SphinxLogHandler

    def __init__(self, dbpath: pathlib.Path):
        self.db = Database(dbpath)
        self.log = typing.cast(SphinxLogHandler, None)


class Sphinx(_Sphinx):
    """A regular sphinx application with a few extra fields."""

    esbonio: Esbonio

    def __init__(self, *args, **kwargs):
        dbpath = pathlib.Path(kwargs["outdir"], "esbonio.db").resolve()
        self.esbonio = Esbonio(dbpath)

        super().__init__(*args, **kwargs)
