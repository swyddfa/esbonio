from __future__ import annotations

import inspect
import typing

from lsprotocol import types as lsp

from esbonio import server
from esbonio.sphinx_agent import types

if typing.TYPE_CHECKING:
    from typing import Any
    from typing import Coroutine
    from typing import Dict
    from typing import List
    from typing import Optional
    from typing import Union

    from esbonio.server import Uri


class RoleProvider:
    """Base class for role providers."""

    def get_role(
        self, uri: Uri, name: str
    ) -> Union[Optional[types.Role], Coroutine[Any, Any, Optional[types.Role]]]:
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
    ) -> Union[
        Optional[List[types.Role]], Coroutine[Any, Any, Optional[List[types.Role]]]
    ]:
        """Givem a completion context, suggest roles that may be used."""
        return None


class RoleTargetProvider:
    """Base class for role target providers."""

    def suggest_targets(
        self, context: server.CompletionContext, **kwargs
    ) -> Union[
        Optional[List[lsp.CompletionItem]],
        Coroutine[Any, Any, Optional[List[lsp.CompletionItem]]],
    ]:
        """Givem a completion context, suggest role targets that may be used."""
        return None


class RolesFeature(server.LanguageFeature):
    """Backend support for roles.

    It's this language feature's responsibility to provide an API that exposes the
    information a frontend feature may want.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._role_providers: Dict[int, RoleProvider] = {}
        self._target_providers: Dict[str, RoleTargetProvider] = {}

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
    ) -> List[types.Role]:
        """Suggest roles that may be used, given a completion context.

        Parameters
        ----------
        context
           The completion context
        """
        items: List[types.Role] = []

        for provider in self._role_providers.values():
            try:
                result: Optional[List[types.Role]] = None

                aresult = provider.suggest_roles(context)
                if inspect.isawaitable(aresult):
                    result = await aresult

                if result:
                    items.extend(result)
            except Exception:
                name = type(provider).__name__
                self.logger.error("Error in '%s.suggest_roles'", name, exc_info=True)

        return items

    async def get_role(self, uri: Uri, name: str) -> Optional[types.Role]:
        """Return the definition of the given role name.

        Parameters
        ----------
        uri
           The uri of the document in which the role name appears

        name
           The name of the role, as the user would type into a document.

        Returns
        -------
        Optional[types.Role]
           The role's definition, if known
        """
        for provider in self._role_providers.values():
            try:
                result: Optional[types.Role] = None

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
    ) -> List[lsp.CompletionItem]:
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
                result: Optional[List[lsp.CompletionItem]] = None

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
