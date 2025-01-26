from __future__ import annotations

import inspect
import json
import pathlib
import re
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
    from collections.abc import Awaitable
    from typing import Any
    from typing import Callable
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

    spec: type[T]
    """The subscription's class definition."""

    context: ConfigurationContext
    """The context for this subscription."""


@attrs.define
class ConfigChangeEvent(Generic[T]):
    """Is sent to subscribers when a configuration change occurs."""

    scope: str
    """The scope at which this configuration change occured."""

    value: T
    """The latest configuration value."""

    previous: T | None = None
    """The previous configuration value, (if any)."""


VARIABLE = re.compile(r"\$\{(\w+)\}")


@attrs.define(frozen=True)
class ConfigurationContext:
    """The context in which configuration variables are evaluated."""

    file_scope: str
    """The uri of the file scope of this context."""

    workspace_scope: str
    """The uri of the workspace scope of this context."""

    @property
    def scope(self) -> str:
        """The effective scope of the config context."""
        return max([self.file_scope, self.workspace_scope], key=len)

    @property
    def scope_path(self) -> str | None:
        """The scope uri as a path."""
        uri = Uri.parse(self.scope)
        return uri.path

    @property
    def scope_fs_path(self) -> str | None:
        """The scope uri as an fs path."""
        uri = Uri.parse(self.scope)
        return uri.fs_path

    def expand(self, config: attrs.AttrsInstance) -> attrs.AttrsInstance:
        """Expand any configuration variables in the given config value."""
        for name in attrs.fields_dict(type(config)):
            value = getattr(config, name)

            # For now, we only support variables that are a string.
            if not isinstance(value, str):
                continue

            if (match := VARIABLE.match(value)) is None:
                continue

            setattr(config, name, self.expand_value(match.group(1)))

        return config

    def expand_value(self, variable: str) -> Any:
        """Return the value for the given variable name."""

        if variable == "scope":
            return self.scope

        if variable == "scopePath":
            return self.scope_path

        if variable == "scopeFsPath":
            return self.scope_fs_path

        raise ValueError(f"Undefined variable: {variable!r}")


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

        self._initialization_options: dict[str, Any] = {}
        """The received initializaion options (if any)"""

        self._workspace_config: dict[str, dict[str, Any]] = {}
        """The cached workspace configuration."""

        self._file_config: dict[str, dict[str, Any]] = {}
        """The cached configuration coming from configuration files."""

        self._subscriptions: dict[
            Subscription, tuple[Any, list[ConfigurationCallback]]
        ] = {}
        """Subscriptions and their last known value"""

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
        spec: type[T],
        callback: ConfigurationCallback,
        scope: Uri | None = None,
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

        context = ConfigurationContext(
            file_scope=file_scope, workspace_scope=workspace_scope
        )
        subscription = Subscription(section, spec, context)

        if new_subscription := subscription not in self._subscriptions:
            self.logger.debug("Creating new subscription: %s", subscription)
            self._subscriptions[subscription] = (None, [])

        value, callbacks = self._subscriptions[subscription]
        callbacks.append(callback)

        if self.server.ready.done():
            # If a value exists, notify the new callback immediately
            if value is not None:
                change_event = ConfigChangeEvent(
                    scope=subscription.context.scope,
                    value=value,
                    previous=None,
                )
                self._invoke_callback(callback, change_event)

            else:
                # Otherwise compute a value and notify all of them
                self._notify_subscription(subscription)

        elif new_subscription:
            self.server.ready.add_done_callback(
                partial(self._notify_subscription, subscription)
            )

    def _notify_subscriptions(self):
        """Notify all subscriptions about configuration changes, if necessary."""

        for subscription in self._subscriptions:
            self._notify_subscription(subscription)

    def _notify_subscription(self, subscription: Subscription, *args):
        """Check a single subscription's value and notify it, if it has changed.

        Parameters
        ----------
        subscription
           The subscription to check
        """

        previous_value, callbacks = self._subscriptions[subscription]
        value = self._get_config(
            subscription.section,
            subscription.spec,
            subscription.context,
        )

        # No need to notify if nothing has changed
        self.logger.debug("Previous: %s", previous_value)
        self.logger.debug("Current: %s", value)
        self._subscriptions[subscription] = value, callbacks

        if previous_value == value:
            return

        change_event = ConfigChangeEvent(
            scope=subscription.context.scope,
            value=value,
            previous=previous_value,
        )
        self.logger.info("%s", change_event)

        for callback in callbacks:
            self._invoke_callback(callback, change_event)

    def _invoke_callback(
        self, callback: ConfigurationCallback, change_event: ConfigChangeEvent
    ):
        """Invoke the given callback

        Parameters
        ----------
        callback
           The callback function to invoke

        change_event
           The change event to send
        """
        try:
            ret = callback(change_event)
            if inspect.iscoroutine(ret):
                self.server.run_task(ret)

        except Exception:
            self.logger.error(
                "Error in configuration callback: %s", callback, exc_info=True
            )

    def get(self, section: str, spec: type[T], scope: Uri | None = None) -> T:
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
        context = ConfigurationContext(
            file_scope=self._uri_to_file_scope(scope),
            workspace_scope=self._uri_to_workspace_scope(scope),
        )

        return self._get_config(section, spec, context)

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
        context = ConfigurationContext(
            file_scope=self._uri_to_file_scope(uri),
            workspace_scope=self._uri_to_workspace_scope(uri),
        )

        return context.scope

    def _get_config(
        self,
        section: str,
        spec: type[T],
        context: ConfigurationContext,
    ) -> T:
        """Get the requested configuration section."""

        self.logger.debug("%s", context)

        # To keep things simple, this method assumes that all available config is already
        # cached locally. Populating the cache is handled elsewhere.
        file_config = self._file_config.get(context.file_scope, {})
        workspace_config = self._workspace_config.get(context.workspace_scope, {})

        # Combine and resolve all the config sources - order matters!
        config = _merge_configs(
            file_config, workspace_config, self._initialization_options
        )
        # self.logger.debug("Full config: %s", json.dumps(config, indent=2))

        # Extract the requested section.
        config_section = config
        for name in section.split("."):
            config_section = config_section.get(name, {})

        self.logger.debug("%s: %s", section, json.dumps(config_section, indent=2))

        try:
            value = self.converter.structure(config_section, spec)
            value = context.expand(value)
            self.logger.debug("%s", value)

            return value
        except Exception:
            self.logger.error(
                "Unable to parse configuation as '%s', using defaults",
                spec.__name__,
                exc_info=True,
            )
            return spec()

    def _uri_to_file_scope(self, uri: Uri | None) -> str:
        folder_uris = list(self._file_config.keys())
        return _uri_to_scope(folder_uris, uri)

    def _uri_to_workspace_scope(self, uri: Uri | None) -> str:
        folder_uris = [f.uri for f in self.workspace.folders.values()]

        if (root_uri := self.workspace.root_uri) is not None:
            folder_uris.append(root_uri)

        return _uri_to_scope(folder_uris, uri)

    def _discover_config_files(self) -> list[pathlib.Path]:
        """Scan the workspace for available configuration files."""
        folder_uris = {f.uri for f in self.workspace.folders.values()}

        if (root_uri := self.workspace.root_uri) is not None:
            folder_uris.add(root_uri)

        paths = []
        for uri in folder_uris:
            if (folder_path := Uri.parse(uri).fs_path) is None:
                continue

            self.logger.debug("Looking for pyproject.toml files in: '%s'", folder_path)
            for p in pathlib.Path(folder_path).glob("**/pyproject.toml"):
                self.logger.debug("Found '%s'", p)
                paths.append(p)

        return paths

    def update_file_configuration(self, paths: list[pathlib.Path] | None = None):
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
            results = await self.server.workspace_configuration_async(params)
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


def _uri_to_scope(known_scopes: list[str], uri: Uri | None) -> str:
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


def _merge_configs(*configs: dict[str, Any]):
    """Recursively merge all the given configuration sources together.

    The last config given takes precedence.
    """
    final = {}
    all_keys: set[str] = set()

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
