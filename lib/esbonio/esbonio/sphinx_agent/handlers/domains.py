from __future__ import annotations

import typing

from docutils import nodes
from sphinx import addnodes

from .. import types
from ..app import Database
from ..app import Sphinx
from ..util import as_json

if typing.TYPE_CHECKING:
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
        self._info: dict[tuple[str, str, str, str], tuple[str | None, str | None]] = {}

        # Needs to run late, but before the handler in ./roles.py
        app.connect("builder-inited", self.init_db, priority=998)

        app.connect("doctree-read", self.doctree_read)
        app.connect("object-description-transform", self.object_defined)
        app.connect("build-finished", self.commit)

    def init_db(self, app: Sphinx):
        """Prepare the database."""
        projects = index_intersphinx_projects(app)
        project_names = [p[0] for p in projects]

        for domain in app.env.domains.values():
            index_domain_directives(app, domain)
            index_domain_roles(app, domain, project_names)

    def doctree_read(self, app: Sphinx, doctree: nodes.document):
        """Extract information from the given doctree.

        Currently only used to get the location of ``:ref:`` targets
        """
        for node in doctree.traverse(condition=nodes.target):
            if (label := node.attributes.get("refid")) is None:
                continue

            if (source := node.source) is None or (line := node.line) is None:
                continue

            location = as_json(
                types.Location(
                    uri=str(types.Uri.for_file(source)),
                    range=types.Range(
                        start=types.Position(line=line - 1, character=0),
                        end=types.Position(line=line, character=0),
                    ),
                )
            )

            key = (label, "std", "label", app.env.docname)
            self._info[key] = ("", location)

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
                desc, location = self._get_object_details(
                    app, objname, name, objtype, docname
                )

                if objname == (display := str(dispname)):
                    display = "-"

                rows.append(
                    (objname, display, name, objtype, docname, None, desc, location)
                )

        app.esbonio.db.insert_values(OBJECTS_TABLE, rows)
        # self._info.clear()

    def _get_object_details(
        self, app: Sphinx, objname: str, domain: str, objtype: str, docname: str
    ) -> tuple[str | None, str | None]:
        """Get additional details about the given object."""
        desc, location = self._info.get(
            (objname, domain, objtype, docname), (None, None)
        )

        if location is None and f"{domain}:{objtype}" == "std:doc":
            docpath = app.env.doc2path(objname)
            location = as_json(
                types.Location(
                    uri=str(types.Uri.for_file(docpath)),
                    range=types.Range(
                        start=types.Position(line=0, character=0),
                        end=types.Position(line=1, character=0),
                    ),
                )
            )

        return desc, location

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
                        start=types.Position(line=line - 1, character=0),
                        end=types.Position(line=line, character=0),
                    ),
                )
            )
        else:
            location = None

        key = (name, domain, objtype, docname)
        self._info[key] = (description, location)


def index_domain_directives(app: Sphinx, domain: Domain):
    """Index the directives in the given domain.

    Parameters
    ----------
    app
       The application instance

    domain
       The domain to index
    """
    for name, directive in domain.directives.items():
        app.esbonio.add_directive(f"{domain.name}:{name}", directive, [])


def index_domain_roles(app: Sphinx, domain: Domain, projects: list[str] | None):
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
    target_types: dict[str, set[str]] = {}

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


def index_intersphinx_projects(app: Sphinx) -> list[tuple[str, str, str, str]]:
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

    projects: list[tuple[str, str, str, str]] = []
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
