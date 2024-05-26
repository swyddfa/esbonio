from __future__ import annotations

import typing

from sphinx import addnodes

from .. import types
from ..app import Database
from ..app import Sphinx
from ..util import as_json

if typing.TYPE_CHECKING:
    from typing import Dict
    from typing import Optional
    from typing import Tuple

OBJECTS_TABLE = Database.Table(
    "objects",
    [
        Database.Column(name="name", dtype="TEXT"),
        Database.Column(name="display", dtype="TEXT"),
        Database.Column(name="domain", dtype="TEXT"),
        Database.Column(name="objtype", dtype="TEXT"),
        Database.Column(name="docname", dtype="TEXT"),
        Database.Column(name="description", dtype="TEXT"),
        Database.Column(name="location", dtype="JSON"),
    ],
)


class DomainObjects:
    """Discovers and indexes domain objects."""

    def __init__(self, app: Sphinx):
        self._info: Dict[
            Tuple[str, str, str, str], Tuple[Optional[str], Optional[str]]
        ] = {}

        app.connect("builder-inited", self.init_db)
        app.connect("object-description-transform", self.object_defined)
        app.connect("build-finished", self.commit)

    def init_db(self, app: Sphinx):
        """Prepare the database."""
        app.esbonio.db.ensure_table(OBJECTS_TABLE)

    def commit(self, app, exc):
        """Commit changes to the database.

        The only way to guarantee we discover all objects, from all domains correctly,
        is to call the ``get_objects()`` method on each domain. This means we process
        every object, every time we build.

        I will be *very* surprised if this never becomes a performance issue, but we
        will have to think of a smarter approach when it comes to it.
        """
        app.esbonio.db.clear_table(OBJECTS_TABLE)
        rows = []

        for name, domain in app.env.domains.items():
            for objname, dispname, objtype, docname, _, _ in domain.get_objects():
                desc, location = self._info.get(
                    (objname, name, objtype, docname), (None, None)
                )
                rows.append(
                    (objname, str(dispname), name, objtype, docname, desc, location)
                )

        app.esbonio.db.insert_values(OBJECTS_TABLE, rows)
        self._info.clear()

    def object_defined(
        self, app: Sphinx, domain: str, objtype: str, content: addnodes.desc_content
    ):
        """Record additional information about a domain object.

        Despite having a certain amount of structure to them (thanks to the API),
        domains can still do arbitrary things - take a peek at the implementations of
        the ``std``, ``py`` and ``cpp`` domains!

        So while this will never be perfect, this method is called each time the
        ``object-description-transform`` event is fired and attempts to extract the
        object's description and precise location.

        The trick however, is linking these items up with the correct object
        """

        sig = content.parent[0]

        try:
            name = sig["ids"][0]  # type: ignore[index]
        except Exception:
            return

        docname = app.env.docname
        description = content.astext()

        if (source := sig.source) is not None and (line := sig.line) is not None:
            location = as_json(
                types.Location(
                    uri=str(types.Uri.for_file(source)),
                    range=types.Range(
                        start=types.Position(line=line, character=0),
                        end=types.Position(line=line + 1, character=0),
                    ),
                )
            )
        else:
            location = None

        key = (name, domain, objtype, docname)
        self._info[key] = (description, location)


def setup(app: Sphinx):
    DomainObjects(app)
