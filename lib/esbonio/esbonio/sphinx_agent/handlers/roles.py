import inspect
from typing import Any
from typing import List
from typing import Optional

from docutils.parsers.rst import roles as docutils_roles

from .. import types
from ..app import Database
from ..app import Sphinx
from ..util import as_json

ROLES_TABLE = Database.Table(
    "roles",
    [
        Database.Column(name="name", dtype="TEXT"),
        Database.Column(name="implementation", dtype="TEXT"),
        Database.Column(name="location", dtype="JSON"),
    ],
)


def get_impl_name(role: Any) -> str:
    try:
        return f"{role.__module__}.{role.__name__}"
    except AttributeError:
        return f"{role.__module__}.{role.__class__.__name__}"


def get_impl_location(impl: Any) -> Optional[str]:
    """Get the implementation location of the given directive"""

    try:
        if (filepath := inspect.getsourcefile(impl)) is None:
            return None

        uri = types.Uri.for_file(filepath).resolve()
        source, line = inspect.getsourcelines(impl)

        location = types.Location(
            uri=str(uri),
            range=types.Range(
                start=types.Position(line=line - 1, character=0),
                end=types.Position(line=line + len(source), character=0),
            ),
        )

        return as_json(location)
    except Exception:
        # TODO: Log the error somewhere..
        return None


def index_roles(app: Sphinx):
    """Index all the roles that are available to this app."""

    roles: List[types.Directive] = []
    found_roles = {
        **docutils_roles._roles,  # type: ignore[attr-defined]
        **docutils_roles._role_registry,  # type: ignore[attr-defined]
    }

    for name, role in found_roles.items():
        if role == docutils_roles.unimplemented_role:
            continue

        roles.append((name, get_impl_name(role), None))

    for prefix, domain in app.env.domains.items():
        for name, role in domain.roles.items():
            roles.append(
                (
                    f"{prefix}:{name}",
                    get_impl_name(role),
                    None,
                )
            )

    app.esbonio.db.ensure_table(ROLES_TABLE)
    app.esbonio.db.clear_table(ROLES_TABLE)
    app.esbonio.db.insert_values(ROLES_TABLE, roles)


def setup(app: Sphinx):
    app.connect("builder-inited", index_roles)
