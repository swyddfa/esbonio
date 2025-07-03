from __future__ import annotations

import json
import logging
import os
import pathlib
import typing

from lsprotocol import types as lsp

from esbonio import server
from esbonio.server.features import roles
from esbonio.server.features.project_manager import ProjectManager
from esbonio.sphinx_agent import types

if typing.TYPE_CHECKING:
    import cattrs

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

    def __init__(
        self,
        logger: logging.Logger,
        converter: cattrs.Converter,
        manager: ProjectManager,
    ):
        self.manager = manager
        self.logger = logger
        self.converter = converter

    async def find_target_definition(  # type: ignore
        self,
        context: server.DefinitionContext,
        target: str,
        *,
        obj_types: list[str] | None,
        projects: list[str] | None,
        **kwargs,
    ) -> list[lsp.Location] | None:
        """Find the definition(s) for the given role target."""
        if obj_types is None:
            self.logger.debug("Unable to find definitions, missing object types!")
            return None

        if projects is not None:
            # does not make sense for intersphinx targets...
            return None

        if (project := self.manager.get_project(context.uri)) is None:
            return None

        self.logger.debug("%r, %r, %r, %r", context, target, obj_types, projects)
        db = await project.get_db()
        query = (
            "SELECT "  # noqa: S608
            "  location "
            "FROM objects "
            f'WHERE printf("%s:%s", objects.domain, objects.objtype) in ({", ".join("?" for _ in obj_types)})'
            "       AND objects.name = ?"
        )

        # Hack for absolute docnames...
        if "std:doc" in obj_types and target.startswith("/"):
            target = target[1:]

        cursor = await db.execute(query, (*obj_types, target))
        if (result := await cursor.fetchall()) is None:
            return None

        locations: list[lsp.Location] = []

        for item, *_ in result:
            if item is None:
                continue

            try:
                obj = json.loads(item)
                locations.append(self.converter.structure(obj, lsp.Location))
            except Exception:
                self.logger.exception(
                    "Unable to construct Location instance from value: %r", item
                )

        return locations

    async def hover_target(  # type: ignore
        self,
        context: server.HoverContext,
        target: str,
        *,
        obj_types: list[str] | None,
        projects: list[str] | None,
        **kwargs,
    ) -> str | None:
        """Find the hover text for the given role target."""
        if obj_types is None:
            self.logger.debug("Unable to find hover text, missing object types!")
            return None

        if (project := self.manager.get_project(context.uri)) is None:
            return None

        self.logger.debug("%r, %r, %r, %r", context, target, obj_types, projects)
        db = await project.get_db()
        query = (
            "SELECT "  # noqa: S608
            "  description "
            "FROM objects "
            f'WHERE printf("%s:%s", objects.domain, objects.objtype) in ({", ".join("?" for _ in obj_types)})'
            "       AND objects.name = ?"
        )

        # Hack for absolute docnames...
        if "std:doc" in obj_types and target.startswith("/"):
            target = target[1:]

        cursor = await db.execute(query, (*obj_types, target))
        if (result := await cursor.fetchall()) is None:
            return None

        for item, *_ in result:
            if item is None:
                continue

            return item

        return None

    async def resolve_target_link(
        self,
        context: server.DocumentLinkContext,
        target: str,
        *,
        obj_types: list[str] | None = None,
        projects: list[str] | None = None,
        **kwargs,
    ) -> None | str | tuple[str, str | None]:
        if obj_types is None:
            self.logger.debug("Unable to resolve link, missing object types!")
            return None

        self.logger.debug("%s %s %s %s", context, target, obj_types, projects)
        if projects is not None:
            return await self._resolve_intersphinx_link(
                context, target, obj_types, projects
            )

        if projects is None and "std:doc" in obj_types:
            # Other roles like :ref: do not make sense as the ``textDocument/documentLink``
            # api doesn't support specific locations in a file like goto definition does.
            return await self._resolve_doc_link(context, target)

        return None

    async def _resolve_intersphinx_link(
        self,
        context: server.DocumentLinkContext,
        target: str,
        obj_types: list[str],
        projects: list[str],
    ):
        """Resolve ``textDocument/documentLink`` requests for intersphinx references."""

        if (project := self.manager.get_project(context.uri)) is None:
            return None

        db = await project.get_db()
        query = (
            "SELECT "  # noqa: S608
            '  printf("%s%s", intersphinx_projects.uri, objects.docname) as uri,'
            '  printf("%s v%s", intersphinx_projects.name, intersphinx_projects.version) as source,'
            "  objects.name,"
            "  objects.display "
            "FROM objects JOIN intersphinx_projects "
            "ON objects.project = intersphinx_projects.id "
            f"WHERE objects.project in ({', '.join('?' for _ in projects)}) "
            f'  AND printf("%s:%s", objects.domain, objects.objtype) in ({", ".join("?" for _ in obj_types)})'
            "   AND objects.name = ?"
        )

        cursor = await db.execute(query, (*projects, *obj_types, target))
        if (result := await cursor.fetchone()) is None:
            return None

        uri, source, name, display = result
        display = name if display == "-" else display

        return uri, f"{display} - {source}"

    async def _resolve_doc_link(
        self, context: server.UriContext, target: str
    ) -> str | None:
        """Resolve ``textDocument/documentLink`` requests for local ``:doc:`` references."""

        if (project := self.manager.get_project(context.uri)) is None:
            return None

        if target.startswith("/"):
            docname = target[1:]

        elif (result := await project.uri_to_docname(context.uri)) is None:
            self.logger.debug("Unable to find docname for uri: %r", context.uri)
            return None

        else:
            docname = os.path.normpath(pathlib.Path(result).parent / target)

        return await project.docname_to_uri(docname)

    async def suggest_targets(
        self,
        context: server.CompletionContext,
        *,
        obj_types: list[str] | None = None,
        projects: list[str] | None = None,
        **kwargs,
    ) -> list[lsp.CompletionItem] | None:
        #  TODO: Handle .. currentmodule

        if obj_types is None:
            self.logger.debug("Unable to suggest targets, missing object types!")
            return None

        if (project := self.manager.get_project(context.uri)) is None:
            return None

        items = []
        db = await project.get_db()

        query, parameters = self._prepare_target_query(projects, obj_types)
        cursor = await db.execute(query, parameters)

        for name, display, type_ in await cursor.fetchall():
            kind = TARGET_KINDS.get(type_, lsp.CompletionItemKind.Reference)

            insert_text = None
            if type_ == "doc":
                # Insert an absolute reference, this way the suggestion is always correct.
                insert_text = f"/{name}"

            items.append(
                lsp.CompletionItem(
                    label=name,
                    detail=None if display == "-" else display,
                    kind=kind,
                    insert_text=insert_text,
                ),
            )

        return items

    def _prepare_target_query(self, projects: list[str] | None, obj_types: list[str]):
        """Prepare the query to use when looking up targets."""

        select = "SELECT name, display, objtype FROM objects"
        where = []
        parameters = []

        if projects is None:
            self.logger.debug(
                "Suggesting targets from the local project for types: %s", obj_types
            )
            where.append("project IS NULL")

        else:
            self.logger.debug(
                "Suggesting targets from projects %s for types: %s", projects, obj_types
            )

            placeholders = ", ".join("?" for _ in range(len(projects)))
            where.append(f"project IN ({placeholders})")
            parameters.extend(projects)

        placeholders = ", ".join("?" for _ in range(len(obj_types)))
        where.append(f"printf('%s:%s', domain, objtype) IN ({placeholders})")
        parameters.extend(obj_types)

        query = " ".join([select, "WHERE", " AND ".join(where)])

        return query, tuple(parameters)


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

    async def get_role(self, uri: Uri, name: str) -> types.Role | None:
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
    ) -> list[types.Role] | None:
        """Given a completion context, suggest roles that may be used."""

        if (project := self.manager.get_project(context.uri)) is None:
            return None

        default_domain = await self.get_default_domain(project, context.uri)

        result: list[types.Role] = []
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
        esbonio.logger.getChild("ObjectsProvider"), esbonio.converter, project_manager
    )

    roles_feature.add_role_provider(role_provider)
    roles_feature.add_role_target_provider("objects", obj_provider)
