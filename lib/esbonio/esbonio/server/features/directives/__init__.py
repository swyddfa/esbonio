from __future__ import annotations

import inspect
import typing

from lsprotocol import types as lsp

from esbonio import server
from esbonio.sphinx_agent import types

if typing.TYPE_CHECKING:
    from collections.abc import Coroutine
    from typing import Any


class DirectiveProvider:
    """Base class for directive providers"""

    def suggest_directives(
        self, context: server.CompletionContext
    ) -> (
        list[types.Directive] | None | Coroutine[Any, Any, list[types.Directive] | None]
    ):
        """Given a completion context, suggest directives that may be used."""
        return None


class DirectiveFeature(server.LanguageFeature):
    """'Backend' support for directives.

    It's this language feature's responsibility to provide an API that exposes the
    information a "frontend" language feature may want.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._providers: dict[int, DirectiveProvider] = {}

    def add_provider(self, provider: DirectiveProvider):
        """Register a directive provider.

        Parameters
        ----------
        provider
           The directive provider
        """
        self._providers[id(provider)] = provider

    async def suggest_directives(
        self, context: server.CompletionContext
    ) -> list[types.Directive]:
        """Suggest directives that may be used, given a completion context.

        Parameters
        ----------
        context
           The completion context.
        """
        items: list[types.Directive] = []

        for provider in self._providers.values():
            try:
                result: list[types.Directive] | None = None

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
