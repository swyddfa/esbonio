from __future__ import annotations

import inspect
import typing

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


class RolesFeature(server.LanguageFeature):
    """Backend support for roles.

    It's this language feature's responsibility to provide an API that exposes the
    information a frontend feature may want.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._providers: Dict[int, RoleProvider] = {}

    def add_provider(self, provider: RoleProvider):
        """Register a role provider.

        Parameters
        ----------
        provider
           The role provider
        """
        self._providers[id(provider)] = provider

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

        for provider in self._providers.values():
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


def esbonio_setup(server: server.EsbonioLanguageServer):
    roles = RolesFeature(server)
    server.add_feature(roles)
