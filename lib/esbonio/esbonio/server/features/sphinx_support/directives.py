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

        result: List[directives.Directive] = []
        for name, implementation in await client.get_directives():
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
