from __future__ import annotations

import typing

from lsprotocol import types

from esbonio import server
from esbonio.server.features.roles import RolesFeature
from esbonio.server.features.roles import completion
from esbonio.sphinx_agent.types import RST_DIRECTIVE
from esbonio.sphinx_agent.types import RST_ROLE

if typing.TYPE_CHECKING:
    from typing import List
    from typing import Optional


class RstRoles(server.LanguageFeature):
    """A frontend to roles for reStructuredText syntax."""

    def __init__(self, roles: RolesFeature, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.roles = roles
        self._insert_behavior = "replace"

    completion_triggers = [RST_ROLE]

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

        # If there's no indent, then this can only be a
        # role definition
        indent = context.match.group(1)
        if indent == "":
            return await self.complete_roles(context)

        # Otherwise, search backwards until we find a blank line or an unindent
        # so that we can determine the appropriate context.
        linum = context.position.line - 1

        try:
            line = context.doc.lines[linum]
        except IndexError:
            return await self.complete_roles(context)

        while linum >= 0 and line.startswith(indent):
            linum -= 1
            line = context.doc.lines[linum]

        # Unless we are within a directive's options block, we should offer role
        # suggestions
        if RST_DIRECTIVE.match(line):
            return []

        return await self.complete_roles(context)

    async def complete_targets(self, context: server.CompletionContext):
        return None

    async def complete_roles(
        self, context: server.CompletionContext
    ) -> Optional[List[types.CompletionItem]]:
        """Return completion suggestions for the available roles"""

        language = self.server.get_language_at(context.doc, context.position)
        render_func = completion.get_role_renderer(language, self._insert_behavior)
        if render_func is None:
            return None

        items = []
        for role in await self.roles.suggest_roles(context):
            if (item := render_func(context, role)) is not None:
                items.append(item)

        if len(items) > 0:
            return items

        return None


def esbonio_setup(esbonio: server.EsbonioLanguageServer, roles: RolesFeature):
    rst_roles = RstRoles(roles, esbonio)
    esbonio.add_feature(rst_roles)
