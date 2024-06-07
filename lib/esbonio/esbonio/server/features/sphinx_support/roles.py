from __future__ import annotations

import logging
import typing

from lsprotocol import types as lsp

from esbonio import server
from esbonio.server.features import roles
from esbonio.server.features.project_manager import ProjectManager
from esbonio.sphinx_agent import types

if typing.TYPE_CHECKING:
    from typing import List
    from typing import Optional

    from esbonio.server import Uri
    from esbonio.server.features.project_manager import Project


TARGET_KINDS = {
    "attribute": lsp.CompletionItemKind.Field,
    "doc": lsp.CompletionItemKind.File,
    "class": lsp.CompletionItemKind.Class,
    "envvar": lsp.CompletionItemKind.Variable,
    "function": lsp.CompletionItemKind.Function,
    "method": lsp.CompletionItemKind.Method,
    "module": lsp.CompletionItemKind.Module,
    "term": lsp.CompletionItemKind.Text,
}


class ObjectsProvider(roles.RoleTargetProvider):
    """Expose domain objects as potential role targets"""

    def __init__(self, logger: logging.Logger, manager: ProjectManager):
        self.manager = manager
        self.logger = logger

    async def suggest_targets(  # type: ignore[override]
        self,
        context: server.CompletionContext,
        *,
        obj_types: List[str],
    ) -> Optional[List[lsp.CompletionItem]]:
        self.logger.debug("Suggesting targets for types: %s", obj_types)

        if (project := self.manager.get_project(context.uri)) is None:
            return None

        db = await project.get_db()
        query = " ".join(
            [
                "SELECT name, display, objtype FROM objects",
                "WHERE printf('%s:%s', domain, objtype) IN (",
                ", ".join("?" for _ in range(len(obj_types))),
                ");",
            ]
        )

        items = []
        cursor = await db.execute(query, tuple(obj_types))
        for name, display, type_ in await cursor.fetchall():
            kind = TARGET_KINDS.get(type_, lsp.CompletionItemKind.Reference)
            items.append(
                lsp.CompletionItem(
                    label=name,
                    detail=display,
                    kind=kind,
                ),
            )

        return items


class SphinxRoles(roles.RoleProvider):
    """Support for roles in a sphinx project."""

    def __init__(self, manager: ProjectManager):
        self.manager = manager

    async def get_default_domain(self, project: Project, uri: Uri) -> str:
        """Get the name of the default domain for the given document"""

        # Does the document have a default domain set?
        results = await project.find_symbols(
            uri=str(uri.resolve()),
            kind=lsp.SymbolKind.Class.value,
            detail="default-domain",
        )
        if len(results) > 0:
            default_domain = results[0][1]
        else:
            default_domain = None

        primary_domain = await project.get_config_value("primary_domain")
        return default_domain or primary_domain or "py"

    async def get_role(self, uri: Uri, name: str) -> Optional[types.Role]:
        """Return the role with the given name."""

        if (project := self.manager.get_project(uri)) is None:
            return None

        if (role := await project.get_role(name)) is not None:
            return role

        if (role := await project.get_role(f"std:{name}")) is not None:
            return role

        default_domain = await self.get_default_domain(project, uri)
        return await project.get_role(f"{default_domain}:{name}")

    async def suggest_roles(
        self, context: server.CompletionContext
    ) -> Optional[List[types.Role]]:
        """Given a completion context, suggest roles that may be used."""

        if (project := self.manager.get_project(context.uri)) is None:
            return None

        default_domain = await self.get_default_domain(project, context.uri)

        result: List[types.Role] = []
        for name, implementation in await project.get_roles():
            # std: directives can be used unqualified
            if name.startswith("std:"):
                short_name = name.replace("std:", "")
                result.append(
                    types.Role(name=short_name, implementation=implementation)
                )

            # Also suggest unqualified versions of directives from the currently active domain.
            elif name.startswith(f"{default_domain}:"):
                short_name = name.replace(f"{default_domain}:", "")
                result.append(
                    types.Role(name=short_name, implementation=implementation)
                )

            result.append(types.Role(name=name, implementation=implementation))

        return result


def esbonio_setup(
    esbonio: server.EsbonioLanguageServer,
    project_manager: ProjectManager,
    roles_feature: roles.RolesFeature,
):
    role_provider = SphinxRoles(project_manager)
    obj_provider = ObjectsProvider(
        esbonio.logger.getChild("ObjectsProvider"), project_manager
    )

    roles_feature.add_role_provider(role_provider)
    roles_feature.add_target_provider("objects", obj_provider)
