from typing import List
from typing import Optional

from esbonio import server
from esbonio.server.features import directives
from esbonio.server.features.sphinx_manager import SphinxManager


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

        # TODO .. default-domain:: support
        primary_domain = await client.get_config_value("primary_domain")

        result: List[directives.Directive] = []
        for name, implementation in await client.get_directives():
            # Also suggest unqualified versions of directives from the primary_domain.
            if name.startswith(f"{primary_domain}:"):
                short_name = name.replace(f"{primary_domain}:", "")
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
