from __future__ import annotations

import typing

from lsprotocol import types

from esbonio import server
from esbonio.server.features import directives
from esbonio.server.features.sphinx_manager import SphinxManager

if typing.TYPE_CHECKING:
    from typing import List
    from typing import Optional


class SphinxDirectives(directives.DirectiveProvider):
    """Support for directives in a sphinx project."""

    def __init__(self, manager: SphinxManager):
        self.manager = manager

    async def suggest_directives(
        self, context: server.CompletionContext
    ) -> Optional[List[directives.Directive]]:
        """Given a completion context, suggest directives that may be used."""

        if (client := await self.manager.get_client(context.uri)) is None:
            return None

        # Does the document have a default domain set?
        results = await client.find_symbols(
            uri=str(context.uri.resolve()),
            kind=types.SymbolKind.Class.value,
            detail="default-domain",
        )
        if len(results) > 0:
            default_domain = results[0][1]
        else:
            default_domain = None

        primary_domain = await client.get_config_value("primary_domain")
        active_domain = default_domain or primary_domain or "py"

        result: List[directives.Directive] = []
        for name, implementation in await client.get_directives():
            # Also suggest unqualified versions of directives from the currently active domain.
            if name.startswith(f"{active_domain}:"):
                short_name = name.replace(f"{active_domain}:", "")
                result.append(
                    directives.Directive(name=short_name, implementation=implementation)
                )

            result.append(
                directives.Directive(name=name, implementation=implementation)
            )

        return result


def esbonio_setup(
    sphinx_manager: SphinxManager,
    directive_feature: directives.DirectiveFeature,
):
    provider = SphinxDirectives(sphinx_manager)
    directive_feature.add_provider(provider)
