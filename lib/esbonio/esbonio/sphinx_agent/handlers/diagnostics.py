from typing import Optional

from sphinx.config import Config

from ..app import Database
from ..app import Sphinx
from ..types import Uri
from ..util import as_json

DIAGNOSTICS_TABLE = Database.Table(
    "diagnostics",
    [
        Database.Column(name="uri", dtype="TEXT"),
        Database.Column(name="diagnostic", dtype="JSON"),
    ],
)


def init_db(app: Sphinx, config: Config):
    app.esbonio.db.ensure_table(DIAGNOSTICS_TABLE)


def clear_diagnostics(app: Sphinx, docname: str, source):
    """Clear the diagnostics assocated with the given file."""
    uri = Uri.for_file(app.env.doc2path(docname, base=True))
    app.esbonio.log.diagnostics.pop(uri, None)


def sync_diagnostics(app: Sphinx, exc: Optional[Exception]):
    app.esbonio.db.clear_table(DIAGNOSTICS_TABLE)

    results = []
    diagnostics = app.esbonio.log.diagnostics

    for uri, items in diagnostics.items():
        for item in items:
            results.append((str(uri), as_json(item)))

    app.esbonio.db.insert_values(DIAGNOSTICS_TABLE, results)


def setup(app: Sphinx):
    app.connect("config-inited", init_db)
    app.connect("source-read", clear_diagnostics)

    # TODO: Support for Sphinx v7+
    # app.connect("include-read")

    app.connect("build-finished", sync_diagnostics)
