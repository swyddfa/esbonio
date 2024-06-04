from __future__ import annotations

import typing

from lsprotocol import types

from esbonio import server
from esbonio.server.features.roles import RolesFeature
from esbonio.server.features.roles import completion
from esbonio.sphinx_agent.types import MYST_ROLE

if typing.TYPE_CHECKING:
    from typing import List
    from typing import Optional


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
    ) -> Optional[List[types.CompletionItem]]:
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


def esbonio_setup(esbonio: server.EsbonioLanguageServer, roles: RolesFeature):
    rst_roles = MystRoles(roles, esbonio)
    esbonio.add_feature(rst_roles)
