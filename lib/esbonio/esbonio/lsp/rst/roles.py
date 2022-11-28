import json
from typing import Any
from typing import Dict
from typing import Optional

import docutils.parsers.rst.roles as docutils_roles
import pkg_resources

from esbonio.lsp.roles import RoleLanguageFeature
from esbonio.lsp.roles import Roles
from esbonio.lsp.rst import RstLanguageServer


class Docutils(RoleLanguageFeature):
    """Support for docutils' built-in roles."""

    def __init__(self) -> None:

        self._roles: Optional[Dict[str, Any]] = None
        """Cache for known roles."""

    @property
    def roles(self) -> Dict[str, Any]:
        if self._roles is not None:
            return self._roles

        found_roles = {**docutils_roles._roles, **docutils_roles._role_registry}

        self._roles = {
            k: v
            for k, v in found_roles.items()
            if v != docutils_roles.unimplemented_role
        }

        return self._roles

    def get_implementation(self, role: str, domain: str):
        if domain:
            return None

        return self.roles.get(role, None)

    def index_roles(self) -> Dict[str, Any]:
        return self.roles


def esbonio_setup(rst: RstLanguageServer, roles: Roles):
    documentation = pkg_resources.resource_string("esbonio.lsp.rst", "roles.json")

    roles.add_documentation(json.loads(documentation.decode("utf8")))
    roles.add_feature(Docutils())
