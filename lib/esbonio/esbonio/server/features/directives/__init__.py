from __future__ import annotations

import inspect
import typing

from lsprotocol import types as lsp

from esbonio import server
from esbonio.sphinx_agent import types

from . import providers
from .providers import DirectiveArgumentProvider

if typing.TYPE_CHECKING:
    from collections.abc import Coroutine
    from typing import Any

    from esbonio.server import Uri


class DirectiveProvider:
    """Base class for directive providers"""

    def get_directive(
        self, uri: Uri, name: str
    ) -> types.Directive | None | Coroutine[Any, Any, types.Directive | None]:
        """Return the definition of the given directive, if known

        Parameters
        ----------
        uri
           The uri of the document in which the directive name appears

        name
           The name of the directive, as the user would type in a document
        """
        return None

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

        self._directive_providers: dict[int, DirectiveProvider] = {}
        self._argument_providers: dict[str, DirectiveArgumentProvider] = {}

    def add_directive_provider(self, provider: DirectiveProvider):
        """Register a directive provider.

        Parameters
        ----------
        provider
           The directive provider
        """
        self._directive_providers[id(provider)] = provider

    def add_directive_argument_provider(
        self, name: str, provider: DirectiveArgumentProvider
    ):
        """Register a directive argument provider.

        Parameters
        ----------
        provider
           The directive argument provider
        """
        if (existing := self._argument_providers.get(name)) is not None:
            raise ValueError(
                f"DirectiveArgumentProvider {provider!r} conflicts with existing "
                f"provider: {existing!r}"
            )

        self._argument_providers[name] = provider

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

        for provider in self._directive_providers.values():
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

    async def get_directive(self, uri: Uri, name: str) -> types.Directive | None:
        """Return the definition of the given directive name.

        Parameters
        ----------
        uri
           The uri of the document in which the directive name appears

        name
           The name of the directive, as the user would type into a document.

        Returns
        -------
        types.Directive | None
           The directive's definition, if known
        """
        for provider in self._directive_providers.values():
            try:
                result: types.Directive | None = None

                aresult = provider.get_directive(uri, name)
                if inspect.isawaitable(aresult):
                    result = await aresult

                if result is not None:
                    return result
            except Exception:
                name = type(provider).__name__
                self.logger.error("Error in '%s.get_directive'", name, exc_info=True)

        return None

    async def find_argument_definition(
        self, context: server.DefinitionContext, directive_name: str, argument: str
    ) -> list[lsp.Location] | None:
        """Find the definition of the directive's argument.

        Parameters
        ----------
        context
           The definition context

        directive_name
           The directive to find the argument definition for

        argument
           The directive's argument

        Returns
        -------
        list[lsp.Location] | None
           The argument's defintion(s), if known
        """
        if (directive := await self.get_directive(context.uri, directive_name)) is None:
            self.logger.debug("Unknown directive '%s'", directive_name)
            return None

        if not directive.argument_providers:
            return None

        self.logger.debug(
            "Finding argument defintion for directive: '%s' (%s)",
            directive.name,
            directive.implementation,
        )

        for spec in directive.argument_providers:
            if (provider := self._argument_providers.get(spec.name)) is None:
                self.logger.error("Unknown argument provider: '%s'", spec.name)
                continue

            try:
                result = provider.find_argument_definition(
                    context, argument, **spec.kwargs
                )
                if inspect.isawaitable(result):
                    result = await result

                if result is not None:
                    return result

            except Exception:
                name = type(provider).__name__
                self.logger.exception("Error in '%s.find_argument_definition'", name)

        return None

    async def resolve_argument_link(
        self, context: server.DocumentLinkContext, directive_name: str, argument: str
    ) -> None | str | tuple[str, str | None]:
        """Resolve the link to the given directive argument, if possible.

        Parameters
        ----------
        context
           The document link context

        directive_name
           The directive to resolve the argument for

        argument
           The directive's argument
        """
        if (directive := await self.get_directive(context.uri, directive_name)) is None:
            self.logger.debug("Unknown directive '%s'", directive_name)
            return None

        if not directive.argument_providers:
            return None

        self.logger.debug(
            "Resolving argument link for directive: '%s' (%s)",
            directive.name,
            directive.implementation,
        )

        for spec in directive.argument_providers:
            if (provider := self._argument_providers.get(spec.name)) is None:
                self.logger.error("Unknown argument provider: '%s'", spec.name)
                continue

            try:
                result: None | str | tuple[str, str | None] = None

                aresult = provider.resolve_argument_link(
                    context, argument, **spec.kwargs
                )
                if inspect.isawaitable(aresult):
                    result = await aresult
                else:
                    result = aresult

                if result is not None:
                    return result

            except Exception:
                name = type(provider).__name__
                self.logger.error(
                    "Error in '%s.resolve_argument_link'", name, exc_info=True
                )

        return None

    async def suggest_arguments(
        self, context: server.CompletionContext, directive_name: str
    ) -> list[lsp.CompletionItem]:
        """Suggest directive arguments that may be used, given a completion context.

        Parameters
        ----------
        context
           The completion context

        directive_name
           The directive to suggest arguments for
        """
        if (directive := await self.get_directive(context.uri, directive_name)) is None:
            self.logger.debug("Unknown directive '%s'", directive_name)
            return []

        arguments = []
        self.logger.debug(
            "Suggesting arguments for directive: '%s' (%s)",
            directive.name,
            directive.implementation,
        )

        for spec in directive.argument_providers:
            if (provider := self._argument_providers.get(spec.name)) is None:
                self.logger.error("Unknown argument provider: '%s'", spec.name)
                continue

            try:
                result: list[lsp.CompletionItem] | None = None

                aresult = provider.suggest_arguments(context, **spec.kwargs)
                if inspect.isawaitable(aresult):
                    result = await aresult
                else:
                    result = aresult

                if result is not None:
                    arguments.extend(result)

            except Exception:
                name = type(provider).__name__
                self.logger.error(
                    "Error in '%s.suggest_arguments'", name, exc_info=True
                )

        return arguments


def esbonio_setup(server: server.EsbonioLanguageServer):
    directives = DirectiveFeature(server)
    directives.add_directive_argument_provider(
        "filepath", providers.FilepathProvider(server)
    )
    directives.add_directive_argument_provider(
        "values", providers.ValuesProvider(server)
    )

    server.add_feature(directives)
