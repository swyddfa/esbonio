from __future__ import annotations

import typing

from ..app import Database
from ..app import Sphinx
from ..app import logger
from ..types import Uri
from ..util import as_json

if typing.TYPE_CHECKING:
    from sphinx.config import Config


FILES_TABLE = Database.Table(
    "files",
    [
        Database.Column(name="uri", dtype="TEXT"),
        Database.Column(name="docname", dtype="TEXT"),
        Database.Column(name="urlpath", dtype="TEXT"),
    ],
)

CONFIG_TABLE = Database.Table(
    "config",
    [
        Database.Column(name="name", dtype="TEXT"),
        Database.Column(name="value", dtype="TEXT"),
    ],
)

IGNORED_CONFIG_NAMES = {
    # Declared private by Sphinx in `68af0ac2b`
    "_options",
    # Deprecated/removed in v3.5 and the backwards compatibility code causes issues when
    # dumping the config
    "html_add_permalinks",
}


def init_db(app: Sphinx, config: Config):
    app.esbonio.db.ensure_table(FILES_TABLE)
    app.esbonio.db.ensure_table(CONFIG_TABLE)


def dump_config(app: Sphinx, *args):
    """Dump the user's config into the db so that the parent language server can inspect
    it."""
    app.esbonio.db.clear_table(CONFIG_TABLE)

    values: list[tuple[str, str]] = []
    config = app.config.__getstate__()

    for name, item in config.items():
        if name in IGNORED_CONFIG_NAMES:
            continue

        try:
            values.append(
                (name, as_json(item)),
            )
        except Exception as exc:
            logger.debug(f"Unable to dump config value: {name!r}: {exc}")

    app.esbonio.db.insert_values(CONFIG_TABLE, values)


def build_file_mapping(app: Sphinx, exc: Exception | None):
    """Given a Sphinx application, return a mapping of all known source files to their
    corresponding output files."""

    env = app.env
    builder = app.builder
    files: list[tuple[str, str, str]] = []

    for docname in env.found_docs:
        uri = Uri.for_file(env.doc2path(docname)).resolve()
        build_uri = builder.get_target_uri(docname)

        files.append((str(uri), docname, build_uri))

    # Don't forget any included files.
    # TODO: How best to handle files included in multiple documents?
    for parent_doc, included_docs in env.included.items():
        for docname in included_docs:
            uri = Uri.for_file(env.doc2path(docname)).resolve()
            build_uri = builder.get_target_uri(parent_doc)

            files.append((str(uri), docname, build_uri))

    app.esbonio.db.clear_table(FILES_TABLE)
    app.esbonio.db.insert_values(FILES_TABLE, files)


def setup(app: Sphinx):
    app.connect("config-inited", init_db)
    app.connect("builder-inited", dump_config)
    app.connect("build-finished", build_file_mapping)
