from __future__ import annotations

from lsprotocol import types

from esbonio import server
from esbonio.server.features.roles import RolesFeature
from esbonio.server.features.roles import completion
from esbonio.sphinx_agent.types import MYST_ROLE


class MystRoles(server.LanguageFeature):
    """A frontend to roles for MyST syntax."""

    def __init__(self, roles: RolesFeature, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.roles = roles
        self._insert_behavior = "replace"

    completion_trigger = server.CompletionTrigger(
        patterns=[MYST_ROLE],
        languages={"markdown"},
        characters={"{", "`", "<", "/"},
    )

    definition_trigger = server.DefinitionTrigger(
        patterns=[MYST_ROLE],
        languages={"markdown"},
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
    ) -> list[types.CompletionItem] | None:
        """Provide completion suggestions for roles."""

        groups = context.match.groupdict()
        target = groups["target"]

        # All text matched by the regex
        text = context.match.group(0)
        start, end = context.match.span()

        if target:
            target_index = start + text.find(target)

            # Only trigger target completions if the request was made from within
            # the target part of the role.
            if target_index <= context.position.character <= end:
                return await self.complete_targets(context)

        return await self.complete_roles(context)

    async def complete_targets(self, context: server.CompletionContext):
        """Provide completion suggestions for role targets."""

        render_func = completion.get_role_target_renderer(
            context.language, self._insert_behavior
        )
        if render_func is None:
            return None

        items = []
        role_name = context.match.group("name")
        for target in await self.roles.suggest_targets(context, role_name):
            if (item := render_func(context, target)) is not None:
                items.append(item)

        return items if len(items) > 0 else None

    async def complete_roles(
        self, context: server.CompletionContext
    ) -> list[types.CompletionItem] | None:
        """Return completion suggestions for the available roles"""

        render_func = completion.get_role_renderer(
            context.language, self._insert_behavior
        )
        if render_func is None:
            return None

        items = []
        for role in await self.roles.suggest_roles(context):
            if (item := render_func(context, role)) is not None:
                items.append(item)

        if len(items) > 0:
            return items

        return None

    async def definition(
        self, context: server.DefinitionContext
    ) -> list[types.Location] | None:
        """Find the definition of the requested item"""
        role = context.match.group("name")
        target = context.match.group("target")
        label = context.match.group("label")

        if not label:
            return None

        idx = context.match.group(0).index(target)
        start = context.match.start() + idx
        end = start + len(target)

        if start <= context.position.character <= end:
            return await self.roles.find_target_definition(context, role, label)

        return None

    async def document_link(
        self, context: server.DocumentLinkContext
    ) -> list[types.DocumentLink] | None:
        links = []

        for line, text in enumerate(context.doc.lines):
            for match in MYST_ROLE.finditer(text):
                if not (target := match.group("label")):
                    continue

                name = match.group("name")
                link_target = await self.roles.resolve_target_link(
                    context, name, target
                )

                if link_target is None:
                    continue

                tooltip = None
                if isinstance(link_target, tuple):
                    link_target, tooltip = link_target

                char = "<" if match.group("alias") is not None else "`"
                search = f"{char}{target}"

                idx = match.group(0).index(search) + 1
                start = match.start() + idx
                end = start + len(target)

                links.append(
                    types.DocumentLink(
                        target=link_target,
                        tooltip=tooltip if context.tooltip_support else None,
                        range=types.Range(
                            start=types.Position(line=line, character=start),
                            end=types.Position(line=line, character=end),
                        ),
                    )
                )

        return links if len(links) > 0 else None

    hover_trigger = server.HoverTrigger(
        patterns=[MYST_ROLE],
        languages={"markdown"},
    )

    async def hover(self, context: server.HoverContext) -> types.Hover | None:
        """Find the hover text of the requested item"""
        role = context.match.group("name")
        target = context.match.group("target")
        label = context.match.group("label")

        if not label:
            return None

        idx = context.match.group(0).index(target)
        start = context.match.start() + idx
        end = start + len(target)

        if start <= context.position.character <= end:
            if (text := await self.roles.hover_target(context, role, label)) is None:
                return None
        else:
            return None

        linum = context.position.line
        return types.Hover(
            contents=types.MarkupContent(kind=types.MarkupKind.Markdown, value=text),
            range=types.Range(
                start=types.Position(line=linum, character=start),
                end=types.Position(line=linum, character=end),
            ),
        )


def esbonio_setup(esbonio: server.EsbonioLanguageServer, roles: RolesFeature):
    rst_roles = MystRoles(roles, esbonio)
    esbonio.add_feature(rst_roles)
