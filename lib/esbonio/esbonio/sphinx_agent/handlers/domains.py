from __future__ import annotations

import typing

from sphinx import addnodes

from .. import types
from ..app import Database
from ..app import Sphinx
from ..util import as_json

if typing.TYPE_CHECKING:
    from typing import Dict
    from typing import List
    from typing import Optional
    from typing import Set
    from typing import Tuple

    from sphinx.domains import Domain
    from sphinx.util.typing import Inventory


PROJECTS_TABLE = Database.Table(
    "intersphinx_projects",
    [
        Database.Column(name="id", dtype="TEXT"),
        Database.Column(name="name", dtype="TEXT"),
        Database.Column(name="version", dtype="TEXT"),
        Database.Column(name="uri", dtype="TEXT"),
    ],
)


OBJECTS_TABLE = Database.Table(
    "objects",
    [
        Database.Column(name="name", dtype="TEXT"),
        Database.Column(name="display", dtype="TEXT"),
        Database.Column(name="domain", dtype="TEXT"),
        Database.Column(name="objtype", dtype="TEXT"),
        Database.Column(name="docname", dtype="TEXT"),
        Database.Column(name="project", dtype="TEXT"),
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

        # Needs to run late, but before the handler in ./roles.py
        app.connect("builder-inited", self.init_db, priority=998)
        app.connect("object-description-transform", self.object_defined)
        app.connect("build-finished", self.commit)

    def init_db(self, app: Sphinx):
        """Prepare the database."""
        projects = index_intersphinx_projects(app)
        project_names = [p[0] for p in projects]

        for domain in app.env.domains.values():
            index_domain(app, domain, project_names)

    def commit(self, app, exc):
        """Commit changes to the database.

        The only way to guarantee we discover all objects, from all domains correctly,
        is to call the ``get_objects()`` method on each domain. This means we process
        every object, every time we build.

        I will be *very* surprised if this never becomes a performance issue, but we
        will have to think of a smarter approach when it comes to it.
        """
        app.esbonio.db.clear_table(OBJECTS_TABLE, project=None)
        rows = []

        for name, domain in app.env.domains.items():
            for objname, dispname, objtype, docname, _, _ in domain.get_objects():
                desc, location = self._info.get(
                    (objname, name, objtype, docname), (None, None)
                )

                if objname == (display := str(dispname)):
                    display = "-"

                rows.append(
                    (objname, display, name, objtype, docname, None, desc, location)
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


def index_domain(app: Sphinx, domain: Domain, projects: Optional[List[str]]):
    """Index the roles in the given domain.

    Parameters
    ----------
    app
       The application instance

    domain
       The domain to index

    projects
       The list of known intersphinx projects
    """
    target_types: Dict[str, Set[str]] = {}

    for obj_name, item_type in domain.object_types.items():
        for role_name in item_type.roles:
            target_type = f"{domain.name}:{obj_name}"
            target_types.setdefault(role_name, set()).add(target_type)

    for name, role in domain.roles.items():
        if (item_types := target_types.get(name)) is None:
            app.esbonio.add_role(f"{domain.name}:{name}", role, [])
            continue

        # Add an entry for the local project.
        provider = app.esbonio.create_role_target_provider(
            "objects", obj_types=list(item_types), projects=None
        )
        app.esbonio.add_role(f"{domain.name}:{name}", role, [provider])

        if projects is None or len(projects) == 0:
            continue

        # Add an entry referencing all external projects
        provider = app.esbonio.create_role_target_provider(
            "objects", obj_types=list(item_types), projects=projects
        )
        app.esbonio.add_role(f"external:{domain.name}:{name}", role, [provider])

        # Add an entry dedicated to each external project
        for project in projects:
            provider = app.esbonio.create_role_target_provider(
                "objects", obj_types=list(item_types), projects=[project]
            )
            app.esbonio.add_role(
                f"external+{project}:{domain.name}:{name}", role, [provider]
            )


def index_intersphinx_projects(app: Sphinx) -> List[Tuple[str, str, str, str]]:
    """Index all the projects known to intersphinx.

    Parameters
    ----------
    app
       The application instance

    Returns
    -------
    List[Tuple[str, str, str, str]]
       The list of discovered projects
    """
    app.esbonio.db.ensure_table(OBJECTS_TABLE)
    app.esbonio.db.ensure_table(PROJECTS_TABLE)
    app.esbonio.db.clear_table(PROJECTS_TABLE)

    projects: List[Tuple[str, str, str, str]] = []
    objects = []

    mapping = getattr(app.config, "intersphinx_mapping", {})
    inventory = getattr(app.env, "intersphinx_named_inventory", {})

    for id_, (_, (uri, _)) in mapping.items():
        if (project := inventory.get(id_, None)) is None:
            continue

        app.esbonio.db.clear_table(OBJECTS_TABLE, project=id_)

        # We just need an entry to be able to extract the project name and version
        (name, version, _, _) = next(iter(next(iter(project.values())).values()))

        projects.append((id_, name, version, uri))
        objects.extend(index_intersphinx_objects(id_, uri, project))

    app.esbonio.db.insert_values(PROJECTS_TABLE, projects)
    app.esbonio.db.insert_values(OBJECTS_TABLE, objects)

    return projects


def index_intersphinx_objects(project_name: str, uri: str, project: Inventory):
    """Index all the objects in the given project."""

    objects = []

    for objtype, items in project.items():
        domain = None
        if ":" in objtype:
            domain, *parts = objtype.split(":")
            objtype = ":".join(parts)

        for objname, (_, _, item_uri, display) in items.items():
            docname = item_uri.replace(uri, "")
            objects.append(
                (objname, display, domain, objtype, docname, project_name, None, None)
            )

    return objects


def setup(app: Sphinx):
    DomainObjects(app)
