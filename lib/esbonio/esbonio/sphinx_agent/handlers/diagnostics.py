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
    filepath = app.env.doc2path(docname, base=True)
    app.esbonio.log.diagnostics.pop(filepath, None)


def sync_diagnostics(app: Sphinx, exc: Optional[Exception]):
    app.esbonio.db.clear_table(DIAGNOSTICS_TABLE)

    results = []
    diagnostics = app.esbonio.log.diagnostics

    for fpath, items in diagnostics.items():
        uri = str(Uri.for_file(fpath).resolve())
        for item in items:
            results.append((uri, as_json(item)))

    app.esbonio.db.insert_values(DIAGNOSTICS_TABLE, results)


def setup(app: Sphinx):
    app.connect("config-inited", init_db)
    app.connect("source-read", clear_diagnostics)

    # TODO
    # app.connect("include-read")

    app.connect("build-finished", sync_diagnostics)
