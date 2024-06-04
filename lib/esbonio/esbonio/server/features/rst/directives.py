from __future__ import annotations

import typing

from lsprotocol import types

from esbonio import server
from esbonio.server.features.directives import DirectiveFeature
from esbonio.server.features.directives import completion
from esbonio.sphinx_agent.types import RST_DIRECTIVE

if typing.TYPE_CHECKING:
    from typing import List
    from typing import Optional


class RstDirectives(server.LanguageFeature):
    """A frontend to directives for reStructuredText syntax."""

    def __init__(self, directives: DirectiveFeature, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.directives = directives
        self._insert_behavior = "replace"

    completion_trigger = server.CompletionTrigger(
        patterns=[RST_DIRECTIVE],
        languages={"rst"},
        characters={".", "`"},
    )

    def initialized(self, params: types.InitializedParams):
        """Called once the initial handshake between client and server has finished."""
        self.configuration.subscribe(
            "esbonio.server.completion",
            server.CompletionConfig,
            self.update_configuration,
        )

    def update_configuration(
        self, event: server.ConfigChangeEvent[server.CompletionConfig]
    ):
        """Called when the user's configuration is updated."""
        self._insert_behavior = event.value.preferred_insert_behavior

    async def completion(
        self, context: server.CompletionContext
    ) -> Optional[List[types.CompletionItem]]:
        """Provide completion suggestions for directives."""

        groups = context.match.groupdict()

        # Are we completing a directive's options?
        if "directive" not in groups:
            return await self.complete_options(context)

        # Don't offer completions for targets
        if (groups["name"] or "").startswith("_"):
            return None

        # Are we completing the directive's argument?
        directive_end = context.match.span()[0] + len(groups["directive"])
        complete_directive = groups["directive"].endswith("::")

        if complete_directive and directive_end < context.position.character:
            return await self.complete_arguments(context)

        return await self.complete_directives(context)

    async def complete_options(self, context: server.CompletionContext):
        return None

    async def complete_arguments(self, context: server.CompletionContext):
        return None

    async def complete_directives(
        self, context: server.CompletionContext
    ) -> Optional[List[types.CompletionItem]]:
        """Return completion suggestions for the available directives."""

        render_func = completion.get_directive_renderer(
            context.language, self._insert_behavior
        )
        if render_func is None:
            return None

        items = []
        for directive in await self.directives.suggest_directives(context):
            if (item := render_func(context, directive)) is not None:
                items.append(item)

        if len(items) > 0:
            return items

        return None


def esbonio_setup(esbonio: server.EsbonioLanguageServer, directives: DirectiveFeature):
    rst_directives = RstDirectives(directives, esbonio)
    esbonio.add_feature(rst_directives)
