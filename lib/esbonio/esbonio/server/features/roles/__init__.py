from __future__ import annotations

import inspect
import typing

import attrs
from lsprotocol import types

from esbonio import server
from esbonio.sphinx_agent.types import MYST_ROLE
from esbonio.sphinx_agent.types import RST_DIRECTIVE
from esbonio.sphinx_agent.types import RST_ROLE

from . import completion

if typing.TYPE_CHECKING:
    from typing import Any
    from typing import Coroutine
    from typing import Dict
    from typing import List
    from typing import Optional
    from typing import Union


@attrs.define
class Role:
    """Represents a role."""

    name: str
    """The name of the role, as the user would type in an rst file."""

    implementation: Optional[str]
    """The dotted name of the role's implementation."""


class RoleProvider:
    """Base class for role providers."""

    def suggest_roles(
        self, context: server.CompletionContext
    ) -> Union[Optional[List[Role]], Coroutine[Any, Any, Optional[List[Role]]]]:
        """Givem a completion context, suggest roles that may be used."""
        return None


class RolesFeature(server.LanguageFeature):
    """Support for roles."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._providers: Dict[int, RoleProvider] = {}
        self._insert_behavior = "replace"

    def add_provider(self, provider: RoleProvider):
        """Register a role provider.

        Parameters
        ----------
        provider
           The role provider
        """
        self._providers[id(provider)] = provider

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

    completion_triggers = [MYST_ROLE, RST_ROLE]

    async def completion(
        self, context: server.CompletionContext
    ) -> Optional[List[types.CompletionItem]]:
        """Provide completion suggestions for roles."""

        language = self.server.get_language_at(context.doc, context.position)
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

        # If there's no indent, or this is a markdown document, then this can only be a
        # role definition
        indent = context.match.group(1)
        if indent == "" or language == "markdown":
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
        for role in await self.suggest_roles(context):
            if (item := render_func(context, role)) is not None:
                items.append(item)

        if len(items) > 0:
            return items

        return None

    async def suggest_roles(self, context: server.CompletionContext) -> List[Role]:
        """Suggest roles that may be used, given a completion context.

        Parameters
        ----------
        context
           The completion context
        """
        items: List[Role] = []

        for provider in self._providers.values():
            try:
                result: Optional[List[Role]] = None

                aresult = provider.suggest_roles(context)
                if inspect.isawaitable(aresult):
                    result = await aresult

                if result:
                    items.extend(result)
            except Exception:
                name = type(provider).__name__
                self.logger.error("Error in '%s.suggest_roles'", name, exc_info=True)

        return items


def esbonio_setup(server: server.EsbonioLanguageServer):
    roles = RolesFeature(server)
    server.add_feature(roles)
