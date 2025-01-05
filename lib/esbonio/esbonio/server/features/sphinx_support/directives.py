from __future__ import annotations

import typing

from lsprotocol import types as lsp

from esbonio import server
from esbonio.server.features import directives
from esbonio.server.features.project_manager import ProjectManager
from esbonio.sphinx_agent import types

if typing.TYPE_CHECKING:
    from esbonio.server import Uri
    from esbonio.server.features.project_manager import Project


class SphinxDirectives(directives.DirectiveProvider):
    """Support for directives in a sphinx project."""

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

    async def get_directive(self, uri: Uri, name: str) -> types.Directive | None:
        """Return the directive with the given name."""

        if (project := self.manager.get_project(uri)) is None:
            return None

        if (directive := await project.get_directive(name)) is not None:
            return directive

        if (directive := await project.get_directive(f"std:{name}")) is not None:
            return directive

        default_domain = await self.get_default_domain(project, uri)
        return await project.get_directive(f"{default_domain}:{name}")

    async def suggest_directives(
        self, context: server.CompletionContext
    ) -> list[types.Directive] | None:
        """Given a completion context, suggest directives that may be used."""

        if (project := self.manager.get_project(context.uri)) is None:
            return None

        # Does the document have a default domain set?
        results = await project.find_symbols(
            uri=str(context.uri.resolve()),
            kind=lsp.SymbolKind.Class.value,
            detail="default-domain",
        )
        if len(results) > 0:
            default_domain = results[0][1]
        else:
            default_domain = None

        primary_domain = await project.get_config_value("primary_domain")
        active_domain = default_domain or primary_domain or "py"

        result: list[types.Directive] = []
        for name, implementation in await project.get_directives():
            # std: directives can be used unqualified
            if name.startswith("std:"):
                short_name = name.replace("std:", "")
                result.append(
                    types.Directive(name=short_name, implementation=implementation)
                )

            # Also suggest unqualified versions of directives from the currently active domain.
            elif name.startswith(f"{active_domain}:"):
                short_name = name.replace(f"{active_domain}:", "")
                result.append(
                    types.Directive(name=short_name, implementation=implementation)
                )

            result.append(types.Directive(name=name, implementation=implementation))

        return result


def esbonio_setup(
    project_manager: ProjectManager,
    directive_feature: directives.DirectiveFeature,
):
    provider = SphinxDirectives(project_manager)
    directive_feature.add_directive_provider(provider)
