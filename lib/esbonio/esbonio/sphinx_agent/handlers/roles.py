from __future__ import annotations

import inspect
import json
import pathlib
import typing

from docutils.parsers.rst import roles as docutils_roles
from sphinx.util.logging import getLogger

from .. import types
from ..app import Database
from ..app import Sphinx
from ..util import as_json

if typing.TYPE_CHECKING:
    from typing import Any
    from typing import TypedDict

    class RoleInfo(TypedDict):
        documentation: str
        source: str
        license: str


ROLES_TABLE = Database.Table(
    "roles",
    [
        Database.Column(name="name", dtype="TEXT"),
        Database.Column(name="implementation", dtype="TEXT"),
        Database.Column(name="documentation", dtype="TEXT"),
        Database.Column(name="location", dtype="JSON"),
        Database.Column(name="target_providers", dtype="JSON"),
    ],
)
logger = getLogger(__name__)


def get_impl_name(role: Any) -> str:
    try:
        return f"{role.__module__}.{role.__name__}"
    except AttributeError:
        return f"{role.__module__}.{role.__class__.__name__}"


def get_impl_location(impl: Any) -> types.Location | None:
    """Get the implementation location of the given role"""

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

        return location
    except Exception:
        # TODO: Log the error somewhere..
        return None


def index_roles(app: Sphinx):
    """Index all the roles that are available to this app."""

    roles: dict[str, types.Role] = {}

    # Process the roles registered through Sphinx
    for name, impl, providers in app.esbonio._roles:
        roles[name] = types.Role(name, get_impl_name(impl), target_providers=providers)

    # Look any remaining docutils provided roles
    found_roles = {
        **docutils_roles._roles,  # type: ignore[attr-defined]
        **docutils_roles._role_registry,  # type: ignore[attr-defined]
    }

    for name, role in found_roles.items():
        if role == docutils_roles.unimplemented_role or name in roles:
            continue

        roles[name] = types.Role(name, get_impl_name(role))

    populate_known_roles(app, roles)

    app.esbonio.db.ensure_table(ROLES_TABLE)
    app.esbonio.db.clear_table(ROLES_TABLE)
    app.esbonio.db.insert_values(
        ROLES_TABLE, [r.to_db(as_json) for r in roles.values()]
    )


def setup(app: Sphinx):
    # Ensure that this runs as late as possibile
    app.connect("builder-inited", index_roles, priority=999)


def populate_known_roles(app: Sphinx, roles: dict[str, types.Role]):
    """Add documentation and target provider definitions to the role types we know
    about."""

    role_info = _load_role_info()

    for role in roles.values():
        key = f"{role.name}({role.implementation})"
        if (info := role_info.get(key)) is None:
            continue

        role.documentation = render_docs(info)

    # Add additional information that is best determined at runtime
    _add_filepath_provider_to(roles, app)


def _load_role_info() -> dict[str, RoleInfo]:
    """Load the bundled data on known directives."""

    info: dict[str, RoleInfo] = {}

    try:
        path = pathlib.Path(__file__).parent / "docutils.json"
        items = json.loads(path.read_text())
        info.update(items.get("roles", {}))
    except Exception:
        logger.exception("Unable to load info on docutils roles.")

    try:
        path = pathlib.Path(__file__).parent / "sphinx.json"
        items = json.loads(path.read_text())
        info.update(items.get("roles", {}))
    except Exception:
        logger.exception("Unable to load info on sphinx roles.")

    return info


def render_docs(info: RoleInfo) -> str:
    lines = list(info["documentation"])

    if (source := info.get("source", "")) != "":
        lines.append(f"\n\n[Source]({source})")

    if (link := info.get("license", "")) != "":
        lines.append(f"\n\n[License]({link})")

    return "\n".join(lines)


def _add_filepath_provider_to(roles: dict[str, types.Role], app: Sphinx):
    """Add a target provider that returns filepaths relative to the given sphinx project
    to the relevant roles.."""

    filepath_provider = types.Role.TargetProvider("filepath", {"root": app.srcdir})

    for name in ["download"]:
        if (role := roles.get(name)) is not None:
            role.target_providers = [filepath_provider]
