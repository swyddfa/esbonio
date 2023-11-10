from __future__ import annotations

import json
import typing
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Type
from typing import TypeVar

import attrs
from lsprotocol import types
from pygls.capabilities import get_capability

from ._uri import Uri

if typing.TYPE_CHECKING:
    from .server import EsbonioLanguageServer

T = TypeVar("T")


class WorkspaceConfiguration:
    """Manages the configuration values for the server.

    This will looks configuration in the following locations, in descending order of
    priority.

    - The server's ``initializationOptions``
    - ``workspace/configuration`` requests
    - A relevant configuration file

    **Note:** This assumes that a user's client is *either* going to be using
    ``initializationOptions`` *or* ``workspace/configuration`` not both. Any wierdness
    caused by combining both will (probably) not be fixed.

    **Note:** ``initializationOptions`` will implictly work at the global scope. There
    will be not multi-root/multi-project support using ``initializationOptions``. Use
    ``workspace/configuration`` or config files instead.
    """

    def __init__(self, server: EsbonioLanguageServer):
        self.server = server
        """The language server"""

        self.logger = server.logger.getChild("Configuration")
        """The logger instance to use"""

        self._initialization_options: Dict[str, Any] = {}
        """The received initializaion options (if any)"""

        self._workspace_config: Dict[str, Dict[str, Any]] = {}
        """The cached workspace configuration."""

        self._file_config: Dict[str, Dict[str, Any]] = {}
        """The cached configuration coming from configuration files."""

    @property
    def initialization_options(self):
        return self._initialization_options

    @initialization_options.setter
    def initialization_options(self, value):
        """Ensure the init options are namespaced."""
        if value is None or value == {}:
            return

        if "esbonio" not in value:
            value = dict(esbonio=value)

        self._initialization_options = value

    @property
    def converter(self):
        return self.server.converter

    @property
    def workspace(self):
        return self.server.workspace

    @property
    def supports_workspace_config(self):
        """Indicates if the client supports ``workspace/configuration`` requests."""
        return get_capability(
            self.server.client_capabilities, "workspace.configuration", False
        )

    def get(
        self, section: str, spec: Type[T], scope: Optional[Uri] = None
    ) -> Optional[T]:
        """Get the requested configuration section.

        Parameters
        ----------
        section
           The configuration section to retrieve

        spec
           A type representing the expected "shape" of the configuration section

        scope
           An optional uri, specifying the scope in which to lookup the configuration.

        Returns
        -------
        T | None
           The requested configuration section, if available, parsed as an instance of
           ``T``. ``None``, otherwise
        """
        file_scope = self._uri_to_file_scope(scope)
        self.logger.debug("File scope: '%s'", file_scope)

        workspace_scope = self._uri_to_workspace_scope(scope)
        self.logger.debug("Workspace scope: '%s'", workspace_scope)

        # To keep things simple, this method assumes that all available config is already
        # cached locally. Populating the cache is handled elsewhere.
        file_config = self._file_config.get(file_scope, {})
        workspace_config = self._workspace_config.get(workspace_scope, {})

        # Combine and resolve all the config sources - order matters!
        config = _merge_configs(
            file_config, workspace_config, self._initialization_options
        )
        self.logger.debug("Resolved config: %s", json.dumps(config, indent=2))

        # Extract the requested section.
        config_section = config
        for name in section.split("."):
            config_section = config_section.get(name, {})

        self.logger.debug("Config section: %s", json.dumps(config_section, indent=2))

        try:
            return self.converter.structure(config_section, spec)
        except Exception:
            self.logger.error(
                "Unable to parse configuation as '%s', using defaults",
                spec.__name__,
                exc_info=True,
            )
            return spec()

    def _uri_to_file_scope(self, uri: Optional[Uri]) -> str:
        folder_uris = list(self._file_config.keys())
        return _uri_to_scope(folder_uris, uri)

    def _uri_to_workspace_scope(self, uri: Optional[Uri]) -> str:
        folder_uris = [f.uri for f in self.workspace.folders.values()]

        if (root_uri := self.workspace.root_uri) is not None:
            folder_uris.append(root_uri)

        return _uri_to_scope(folder_uris, uri)

    async def update_workspace_configuration(self):
        """Update the internal cache of the client's workspace configuration."""
        if not self.supports_workspace_config:
            return

        # Request configuration at the global scope, and at each workspace.
        scopes = [None] + [f.uri for f in self.workspace.folders.values()]
        if (root_uri := self.workspace.root_uri) is not None and root_uri not in scopes:
            scopes.append(root_uri)

        params = types.ConfigurationParams(
            items=[
                types.ConfigurationItem(section="esbonio", scope_uri=scope)
                for scope in scopes
            ]
        )
        self.logger.debug(
            "workspace/configuration: %s",
            json.dumps(self.converter.unstructure(params), indent=2),
        )

        try:
            results = await self.server.get_configuration_async(params)
        except Exception:
            self.logger.error("Unable to get workspace configuration", exc_info=True)
            return

        for scope, result in zip(scopes, results):
            self.logger.debug(
                "'%s' configuration: %s", scope, json.dumps(result, indent=2)
            )
            if "esbonio" not in result:
                result = dict(esbonio=result)

            self._workspace_config[scope or ""] = result


def _uri_to_scope(known_scopes: List[str], uri: Optional[Uri]) -> str:
    """Convert the given uri to a scope or the empty string if none could be found.

    Parameters
    ----------
    known_scopes
       The collection of known scopes.

    uri
       The uri to convert

    Returns
    -------
    str
        The scope to use
    """
    if uri is None:
        return ""

    uri = uri.resolve()
    known_uris = [str(Uri.parse(u).resolve()) for u in known_scopes]

    candidates = [scope for scope in known_uris if str(uri).startswith(scope)]
    if len(candidates) == 0:
        return ""

    # Return the most specific match.
    return sorted(candidates, key=len, reverse=True)[0]


def _merge_configs(*configs: Dict[str, Any]):
    """Recursively merge all the given configuration sources together.

    The last config given takes precedence.
    """
    final = {}
    all_keys: Set[str] = set()

    for c in configs:
        all_keys.update(c.keys())

    for k in all_keys:
        values = [
            v for c in configs if (v := c.get(k, attrs.NOTHING)) is not attrs.NOTHING
        ]

        # Do we need to recurse?
        if isinstance(values[-1], dict):
            # Be sure to only pass dictionary values to _merge_configs.
            final[k] = _merge_configs(*[v for v in values if isinstance(v, dict)])
        else:
            final[k] = values[-1]

    return final
