from __future__ import annotations

import logging
import pathlib
import typing

from sphinx.application import Sphinx as _Sphinx
from sphinx.util import console
from sphinx.util import logging as sphinx_logging_module
from sphinx.util.logging import NAMESPACE as SPHINX_LOG_NAMESPACE

from . import types
from .database import Database
from .log import DiagnosticFilter

if typing.TYPE_CHECKING:
    from typing import IO
    from typing import Any
    from typing import Dict
    from typing import List
    from typing import Optional
    from typing import Set
    from typing import Tuple
    from typing import Type

    from sphinx.domains import Domain

    RoleDefinition = Tuple[str, Any, List[types.Role.TargetProvider]]

sphinx_logger = logging.getLogger(SPHINX_LOG_NAMESPACE)
sphinx_log_setup = sphinx_logging_module.setup


def setup_logging(app: Sphinx, status: IO, warning: IO):
    # Run the usual setup
    sphinx_log_setup(app, status, warning)

    # Attach our diagnostic filter to the warning handler.
    for handler in sphinx_logger.handlers:
        if handler.level == logging.WARNING:
            handler.addFilter(app.esbonio.log)


class Esbonio:
    """Esbonio specific functionality."""

    db: Database

    log: DiagnosticFilter

    def __init__(self, dbpath: pathlib.Path, app: _Sphinx):
        self.db = Database(dbpath)
        self.log = DiagnosticFilter(app)

        self._roles: List[RoleDefinition] = []
        """Roles captured during Sphinx startup."""

    def add_role(
        self,
        name: str,
        role: Any,
        target_providers: Optional[List[types.Role.TargetProvider]] = None,
    ):
        """Register a role with esbonio.

        Parameters
        ----------
        name
           The name of the role, as the user would type in a document

        role
           The role's implementation

        target_providers
           A list of target providers for the role
        """
        self._roles.append((name, role, target_providers or []))

    @staticmethod
    def create_role_target_provider(name: str, **kwargs) -> types.Role.TargetProvider:
        """Create a new role target provider

        Parameters
        ----------
        name
           The name of the provider

        kwargs
           Additional arguments to pass to the provider instance

        Returns
        -------
        types.Role.TargetProvider
           The target provider
        """
        return types.Role.TargetProvider(name, kwargs)


class Sphinx(_Sphinx):
    """An extended sphinx application that integrates with esbonio."""

    esbonio: Esbonio

    def __init__(self, *args, **kwargs):
        # Disable color codes
        console.nocolor()

        # Add in esbonio specific functionality
        self.esbonio = Esbonio(
            dbpath=pathlib.Path(kwargs["outdir"], "esbonio.db").resolve(),
            app=self,
        )

        # Override sphinx's usual logging setup function
        sphinx_logging_module.setup = setup_logging  # type: ignore

        super().__init__(*args, **kwargs)

    def add_role(self, name: str, role: Any, override: bool = False):
        super().add_role(name, role, override)
        self.esbonio.add_role(name, role)

    def add_domain(self, domain: Type[Domain], override: bool = False) -> None:
        super().add_domain(domain, override)

        target_types: Dict[str, Set[str]] = {}

        for obj_name, item_type in domain.object_types.items():
            for role_name in item_type.roles:
                target_type = f"{domain.name}:{obj_name}"
                target_types.setdefault(role_name, set()).add(target_type)

        for name, role in domain.roles.items():
            providers = []
            if (item_types := target_types.get(name)) is not None:
                providers.append(
                    self.esbonio.create_role_target_provider(
                        "objects", obj_types=list(item_types)
                    )
                )

            self.esbonio.add_role(f"{domain.name}:{name}", role, providers)
