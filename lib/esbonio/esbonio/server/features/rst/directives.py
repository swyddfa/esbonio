from __future__ import annotations

from lsprotocol import types

from esbonio import server
from esbonio.server.features.directives import DirectiveFeature
from esbonio.server.features.directives import completion
from esbonio.sphinx_agent.types import RST_DIRECTIVE


class RstDirectives(server.LanguageFeature):
    """A frontend to directives for reStructuredText syntax."""

    def __init__(self, directives: DirectiveFeature, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.directives = directives
        self._insert_behavior = "replace"

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

    completion_trigger = server.CompletionTrigger(
        patterns=[RST_DIRECTIVE],
        languages={"rst"},
        characters={".", "`"},
    )

    async def completion(
        self, context: server.CompletionContext
    ) -> list[types.CompletionItem] | None:
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

    async def complete_arguments(
        self, context: server.CompletionContext
    ) -> list[types.CompletionItem] | None:
        """Return completion suggestions for the current directive's argument"""

        render_func = completion.get_directive_argument_renderer(
            context.language, self._insert_behavior
        )
        if render_func is None:
            return None

        items = []
        directive_name = context.match.group("name")
        suggestions = await self.directives.suggest_arguments(context, directive_name)

        for argument in suggestions:
            if (item := render_func(context, argument)) is not None:
                items.append(item)

        return items if len(items) > 0 else None

    async def complete_directives(
        self, context: server.CompletionContext
    ) -> list[types.CompletionItem] | None:
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

    definition_trigger = server.DefinitionTrigger(
        patterns=[RST_DIRECTIVE],
        languages={"rst"},
    )

    async def definition(
        self, context: server.DefinitionContext
    ) -> list[types.Location] | None:
        """Find the definition of the requested item"""
        directive = context.match.group("name")
        argument = context.match.group("argument")

        if not argument:
            return None

        start = context.match.group(0).index(argument)
        end = start + len(argument)

        if start <= context.position.character <= end:
            return await self.directives.find_argument_definition(
                context, directive, argument
            )

        return None

    async def document_link(
        self, context: server.DocumentLinkContext
    ) -> list[types.DocumentLink] | None:
        links = []

        for line, text in enumerate(context.doc.lines):
            for match in RST_DIRECTIVE.finditer(text):
                if "::" not in match.group("directive"):
                    continue

                if not (argument := match.group("argument")):
                    continue

                name = match.group("name")
                target = await self.directives.resolve_argument_link(
                    context, name, argument
                )

                if target is None:
                    continue

                tooltip = None
                if isinstance(target, tuple):
                    target, tooltip = target

                idx = match.group(0).index(argument)
                start = match.start() + idx
                end = start + len(argument)

                links.append(
                    types.DocumentLink(
                        target=target,
                        tooltip=tooltip if context.tooltip_support else None,
                        range=types.Range(
                            start=types.Position(line=line, character=start),
                            end=types.Position(line=line, character=end),
                        ),
                    )
                )

        return links if len(links) > 0 else None

    hover_trigger = server.HoverTrigger(
        patterns=[RST_DIRECTIVE],
        languages={"rst"},
    )

    async def hover(self, context: server.HoverContext) -> types.Hover | None:
        """Find the hover text of the item under the cursor."""

        groups = context.match.groupdict()

        # Are we hovering a directive's options?
        if "directive" not in groups:
            return None

        # Don't offer hovers for targets
        if (groups["name"] or "").startswith("_"):
            return None

        # Are we hovering the directive's argument?
        directive_end = context.match.span()[0] + len(groups["directive"])
        hover_directive = groups["directive"].endswith("::")

        if hover_directive and directive_end < context.position.character:
            return None

        return await self.hover_directive(context)

    async def hover_directive(self, context: server.HoverContext) -> types.Hover | None:
        """Find the hover text for the directive under the cursor."""
        uri = context.uri
        pos = context.position
        name = context.match.group("name")

        self.logger.debug("Looking for directive...")
        if (directive := await self.directives.get_directive(uri, name)) is None:
            return None

        self.logger.debug("Hovering directive: %r", directive.name)

        start = context.match.group(0).index(name)
        end = start + len(name)

        return types.Hover(
            contents=types.MarkupContent(
                kind=types.MarkupKind.Markdown,
                value=directive.documentation or directive.implementation or name,
            ),
            range=types.Range(
                start=types.Position(line=pos.line, character=start),
                end=types.Position(line=pos.line, character=end),
            ),
        )


def esbonio_setup(esbonio: server.EsbonioLanguageServer, directives: DirectiveFeature):
    rst_directives = RstDirectives(directives, esbonio)
    esbonio.add_feature(rst_directives)
