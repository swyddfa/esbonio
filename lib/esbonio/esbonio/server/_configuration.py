from __future__ import annotations

import asyncio
import inspect
import json
import pathlib
import traceback
import typing
from functools import partial
from typing import Generic
from typing import TypeVar

import attrs
from lsprotocol import types
from pygls.capabilities import get_capability

from . import Uri

T = TypeVar("T")

if typing.TYPE_CHECKING:
    from typing import Any
    from typing import Awaitable
    from typing import Callable
    from typing import Dict
    from typing import List
    from typing import Optional
    from typing import Set
    from typing import Type
    from typing import Union

    from .server import EsbonioLanguageServer

    ConfigurationCallback = Callable[
        ["ConfigChangeEvent"], Union[Awaitable[None], None]
    ]


try:
    import tomllib as toml
except ImportError:
    import tomli as toml  # type: ignore[no-redef]


@attrs.define(frozen=True)
class Subscription(Generic[T]):
    """Represents a configuration subscription"""

    section: str
    """The configuration section."""

    spec: Type[T]
    """The subscription's class definition."""

    callback: ConfigurationCallback
    """The subscription's callback."""

    workspace_scope: str
    """The corresponding workspace scope for the subscription."""

    file_scope: str
    """The corresponding file scope for the subscription."""


@attrs.define
class ConfigChangeEvent(Generic[T]):
    """Is sent to subscribers when a configuration change occurs."""

    scope: str
    """The scope at which this configuration change occured."""

    value: T
    """The latest configuration value."""

    previous: Optional[T] = None
    """The previous configuration value, (if any)."""


class Configuration:
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

        self._subscriptions: Dict[Subscription, Any] = {}
        """Subscriptions and their last known value"""

        self._tasks: Set[asyncio.Task] = set()
        """Holds tasks that are currently executing an async config handler."""

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

    def subscribe(
        self,
        section: str,
        spec: Type[T],
        callback: ConfigurationCallback,
        scope: Optional[Uri] = None,
    ):
        """Subscribe to updates to the given configuration section.

        Parameters
        ----------
        section
           The configuration section to subscribe to

        spec
           A class representing the configuration values of interest

        callback
           The function to call when changes are detected.

        scope
           An optional uri, specifying the scope at which to lookup the configuration.
        """
        file_scope = self._uri_to_file_scope(scope)
        workspace_scope = self._uri_to_workspace_scope(scope)
        subscription = Subscription(
            section, spec, callback, workspace_scope, file_scope
        )

        if subscription in self._subscriptions:
            self.logger.debug("Ignoring duplicate subscription: %s", subscription)
            return

        self._subscriptions[subscription] = None

        # Once the server is ready, update all the subscriptions
        self.server.ready.add_done_callback(self._notify_subscriptions)

    def _notify_subscriptions(self, *args):
        """Notify subscriptions about configuration changes, if necessary."""

        for subscription, previous_value in self._subscriptions.items():
            value = self._get_config(
                subscription.section,
                subscription.spec,
                subscription.workspace_scope,
                subscription.file_scope,
            )

            # No need to notify if nothing has changed
            self.logger.debug("Previous: %s", previous_value)
            self.logger.debug("Current: %s", value)
            if previous_value == value:
                continue

            self._subscriptions[subscription] = value
            change_event = ConfigChangeEvent(
                scope=max(
                    [subscription.file_scope, subscription.workspace_scope], key=len
                ),
                value=value,
                previous=previous_value,
            )
            self.logger.info("%s", change_event)

            try:
                ret = subscription.callback(change_event)
                if inspect.iscoroutine(ret):
                    task = asyncio.create_task(ret)
                    task.add_done_callback(partial(self._finish_task, subscription))

            except Exception:
                self.logger.error(
                    "Error in configuration callback: %s",
                    subscription.callback,
                    exc_info=True,
                )

    def _finish_task(self, subscription: Subscription, task: asyncio.Task[None]):
        """Cleanup a finished task."""
        self._tasks.discard(task)

        if (exc := task.exception()) is not None:
            self.logger.error(
                "Error in async configuration handler '%s'\n%s",
                subscription.callback,
                "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
            )

    def get(self, section: str, spec: Type[T], scope: Optional[Uri] = None) -> T:
        """Get the requested configuration section.

        Parameters
        ----------
        section
           The configuration section to retrieve

        spec
           A class representing the configuration values of interest

        scope
           An optional uri, specifying the scope in which to lookup the configuration.

        Returns
        -------
        T
           The requested configuration section parsed as an instance of ``T``.
        """
        file_scope = self._uri_to_file_scope(scope)
        workspace_scope = self._uri_to_workspace_scope(scope)

        return self._get_config(section, spec, workspace_scope, file_scope)

    def scope_for(self, uri: Uri) -> str:
        """Return the configuration scope that corresponds to the given uri.

        Parameters
        ----------
        uri
           The uri to return the scope for

        Returns
        -------
        str
           The scope corresponding with the given uri
        """

        file_scope = self._uri_to_file_scope(uri)
        workspace_scope = self._uri_to_workspace_scope(uri)

        return max([file_scope, workspace_scope], key=len)

    def _get_config(
        self, section: str, spec: Type[T], workspace_scope: str, file_scope: str
    ) -> T:
        """Get the requested configuration section."""

        self.logger.debug("File scope: '%s'", file_scope)
        self.logger.debug("Workspace scope: '%s'", workspace_scope)

        # To keep things simple, this method assumes that all available config is already
        # cached locally. Populating the cache is handled elsewhere.
        file_config = self._file_config.get(file_scope, {})
        workspace_config = self._workspace_config.get(workspace_scope, {})

        # Combine and resolve all the config sources - order matters!
        config = _merge_configs(
            file_config, workspace_config, self._initialization_options
        )
        # self.logger.debug("Full config: %s", json.dumps(config, indent=2))

        # Extract the requested section.
        config_section = config
        for name in section.split("."):
            config_section = config_section.get(name, {})

        self.logger.debug("Resolved config: %s", json.dumps(config_section, indent=2))

        try:
            value = self.converter.structure(config_section, spec)
            self.logger.debug("%s", value)

            return value
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

    def _discover_config_files(self) -> List[pathlib.Path]:
        """Scan the workspace for available configuration files."""
        folder_uris = {f.uri for f in self.workspace.folders.values()}

        if (root_uri := self.workspace.root_uri) is not None:
            folder_uris.add(root_uri)

        paths = []
        for uri in folder_uris:
            if (folder_path := Uri.parse(uri).fs_path) is None:
                continue

            self.logger.debug("Scanning workspace folder: '%s'", folder_path)
            for p in pathlib.Path(folder_path).glob("**/pyproject.toml"):
                self.logger.debug("Found '%s'", p)
                paths.append(p)

        return paths

    def update_file_configuration(self, paths: Optional[List[pathlib.Path]] = None):
        """Update the internal cache of configuration coming from files.

        Parameters
        ----------
        paths
           A list of filepaths to read from.
           If not set, this method will scan each workspace folder for relevant files.
        """
        if paths is None:
            paths = self._discover_config_files()

        for path in paths:
            try:
                data = toml.loads(path.read_text())
                config = dict(esbonio=data.get("tool", {}).get("esbonio", {}))
                scope = str(Uri.for_file(path.parent))

                self._file_config[scope] = config
                self.logger.debug(
                    "File '%s' configuration: %s", scope, json.dumps(config, indent=2)
                )
            except Exception:
                self.logger.error(
                    "Unable to read configuration file: '%s'", exc_info=True
                )

        self._notify_subscriptions()

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
                "Workspace '%s' configuration: %s", scope, json.dumps(result, indent=2)
            )
            # result can be `None`
            result = result or {}

            if "esbonio" not in result:
                result = dict(esbonio=result)

            self._workspace_config[scope or ""] = result

        self._notify_subscriptions()


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
