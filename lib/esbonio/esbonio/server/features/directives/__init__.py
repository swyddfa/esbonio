from __future__ import annotations

import inspect
import typing

import attrs
from lsprotocol import types

from esbonio import server
from esbonio.sphinx_agent.types import MYST_DIRECTIVE
from esbonio.sphinx_agent.types import RST_DIRECTIVE

from . import completion

if typing.TYPE_CHECKING:
    from typing import Any
    from typing import Coroutine
    from typing import Dict
    from typing import List
    from typing import Optional
    from typing import Union


@attrs.define
class Directive:
    """Represents a directive."""

    name: str
    """The name of the directive, as the user would type in an rst file."""

    implementation: Optional[str]
    """The dotted name of the directive's implementation."""


class DirectiveProvider:
    """Base class for directive providers"""

    def suggest_directives(
        self, context: server.CompletionContext
    ) -> Union[
        Optional[List[Directive]], Coroutine[Any, Any, Optional[List[Directive]]]
    ]:
        """Given a completion context, suggest directives that may be used."""
        return None


class DirectiveFeature(server.LanguageFeature):
    """Support for directives."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._providers: Dict[int, DirectiveProvider] = {}
        self._insert_behavior = "replace"

    def add_provider(self, provider: DirectiveProvider):
        """Register a directive provider.

        Parameters
        ----------
        provider
           The directive provider
        """
        self._providers[id(provider)] = provider

    completion_triggers = [RST_DIRECTIVE, MYST_DIRECTIVE]

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
        complete_directive = groups["directive"].endswith(("::", "}"))

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

        language = self.server.get_language_at(context.doc, context.position)
        render_func = completion.get_directive_renderer(language, self._insert_behavior)
        if render_func is None:
            return None

        items = []
        for directive in await self.suggest_directives(context):
            if (item := render_func(context, directive)) is not None:
                items.append(item)

        if len(items) > 0:
            return items

        return None

    async def suggest_directives(
        self, context: server.CompletionContext
    ) -> List[Directive]:
        """Suggest directives that may be used, given a completion context.

        Parameters
        ----------
        context
           The completion context.
        """
        items: List[Directive] = []

        for provider in self._providers.values():
            try:
                result: Optional[List[Directive]] = None

                aresult = provider.suggest_directives(context)
                if inspect.isawaitable(aresult):
                    result = await aresult

                if result:
                    items.extend(result)
            except Exception:
                name = type(provider).__name__
                self.logger.error(
                    "Error in '%s.suggest_directives'", name, exc_info=True
                )

        return items


def esbonio_setup(server: server.EsbonioLanguageServer):
    directives = DirectiveFeature(server)
    server.add_feature(directives)
