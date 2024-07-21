from __future__ import annotations

import inspect
import typing

from lsprotocol import types as lsp

from esbonio import server
from esbonio.sphinx_agent import types

if typing.TYPE_CHECKING:
    from collections.abc import Coroutine
    from typing import Any

    from esbonio.server import Uri


class RoleProvider:
    """Base class for role providers."""

    def get_role(
        self, uri: Uri, name: str
    ) -> types.Role | None | Coroutine[Any, Any, types.Role | None]:
        """Return the definition of the given role, if known.

        Parameters
        ----------
        uri
           The uri of the document in which the role name appears

        name
           The name of the role, as the user would type in a document
        """
        return None

    def suggest_roles(
        self, context: server.CompletionContext
    ) -> list[types.Role] | None | Coroutine[Any, Any, list[types.Role] | None]:
        """Givem a completion context, suggest roles that may be used."""
        return None


class RoleTargetProvider:
    """Base class for role target providers."""

    def suggest_targets(
        self, context: server.CompletionContext, **kwargs
    ) -> (
        list[lsp.CompletionItem]
        | None
        | Coroutine[Any, Any, list[lsp.CompletionItem] | None]
    ):
        """Givem a completion context, suggest role targets that may be used."""
        return None


class RolesFeature(server.LanguageFeature):
    """Backend support for roles.

    It's this language feature's responsibility to provide an API that exposes the
    information a frontend feature may want.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._role_providers: dict[int, RoleProvider] = {}
        self._target_providers: dict[str, RoleTargetProvider] = {}

    def add_role_provider(self, provider: RoleProvider):
        """Register a role provider.

        Parameters
        ----------
        provider
           The role provider
        """
        self._role_providers[id(provider)] = provider

    def add_target_provider(self, name: str, provider: RoleTargetProvider):
        """Register a role target provider.

        Parameters
        ----------
        provider
           The role target provider
        """
        if (existing := self._target_providers.get(name)) is not None:
            raise ValueError(
                f"RoleTargetProvider {provider!r} conflicts with existing "
                f"provider: {existing!r}"
            )

        self._target_providers[name] = provider

    async def suggest_roles(
        self, context: server.CompletionContext
    ) -> list[types.Role]:
        """Suggest roles that may be used, given a completion context.

        Parameters
        ----------
        context
           The completion context
        """
        items: list[types.Role] = []

        for provider in self._role_providers.values():
            try:
                result: list[types.Role] | None = None

                aresult = provider.suggest_roles(context)
                if inspect.isawaitable(aresult):
                    result = await aresult

                if result:
                    items.extend(result)
            except Exception:
                name = type(provider).__name__
                self.logger.error("Error in '%s.suggest_roles'", name, exc_info=True)

        return items

    async def get_role(self, uri: Uri, name: str) -> types.Role | None:
        """Return the definition of the given role name.

        Parameters
        ----------
        uri
           The uri of the document in which the role name appears

        name
           The name of the role, as the user would type into a document.

        Returns
        -------
        types.Role | None
           The role's definition, if known
        """
        for provider in self._role_providers.values():
            try:
                result: types.Role | None = None

                aresult = provider.get_role(uri, name)
                if inspect.isawaitable(aresult):
                    result = await aresult

                if result is not None:
                    return result
            except Exception:
                name = type(provider).__name__
                self.logger.error("Error in '%s.get_role'", name, exc_info=True)

        return None

    async def suggest_targets(
        self, context: server.CompletionContext, role_name: str
    ) -> list[lsp.CompletionItem]:
        """Suggest role targets that may be used, given a completion context.

        Parameters
        ----------
        context
           The completion context

        role_name
           The role to suggest targets for
        """
        if (role := await self.get_role(context.uri, role_name)) is None:
            self.logger.debug("Unknown role '%s'", role_name)
            return []

        targets = []
        self.logger.debug(
            "Suggesting targets for role: '%s' (%s)", role.name, role.implementation
        )

        for spec in role.target_providers:
            if (provider := self._target_providers.get(spec.name)) is None:
                self.logger.error("Unknown target provider: '%s'", spec.name)
                continue

            try:
                result: list[lsp.CompletionItem] | None = None

                aresult = provider.suggest_targets(context, **spec.kwargs)
                if inspect.isawaitable(aresult):
                    result = await aresult

                if result is not None:
                    targets.extend(result)

            except Exception:
                name = type(provider).__name__
                self.logger.error("Error in '%s.suggest_targets'", name, exc_info=True)

        return targets


def esbonio_setup(server: server.EsbonioLanguageServer):
    roles = RolesFeature(server)
    server.add_feature(roles)
