import pathlib
from typing import List
from typing import Optional
from typing import Tuple

from sphinx.config import Config

from ..app import Database
from ..app import Sphinx

FILES_TABLE = Database.Table(
    "files",
    [
        Database.Column(name="path", dtype="TEXT"),
        Database.Column(name="docname", dtype="TEXT"),
        Database.Column(name="uri", dtype="TEXT"),
    ],
)


def init_db(app: Sphinx, config: Config):
    app.esbonio.db.ensure_table(FILES_TABLE)


def build_file_mapping(app: Sphinx, exc: Optional[Exception]):
    """Given a Sphinx application, return a mapping of all known source files to their
    corresponding output files."""

    env = app.env
    builder = app.builder
    files: List[Tuple[str, str, str]] = []

    for docname in env.found_docs:
        path = pathlib.Path(env.doc2path(docname)).resolve()
        build_uri = builder.get_target_uri(docname)

        files.append((str(path), docname, build_uri))

    # Don't forget any included files.
    # TODO: How best to handle files included in multiple documents?
    for parent_doc, included_docs in env.included.items():
        for docname in included_docs:
            path = pathlib.Path(env.doc2path(docname)).resolve()
            build_uri = builder.get_target_uri(parent_doc)

            files.append((str(path), docname, build_uri))

    app.esbonio.db.clear_table(FILES_TABLE)
    app.esbonio.db.insert_values(FILES_TABLE, files)


def setup(app: Sphinx):
    app.connect("config-inited", init_db)
    app.connect("build-finished", build_file_mapping)
