import enum
import json
import logging
import logging.config
import textwrap
from logging.handlers import MemoryHandler
from typing import Any
from typing import Dict
from typing import Optional

import attrs
from lsprotocol import types

from esbonio import server

LOG_LEVELS = {"CRITICAL", "FATAL", "ERROR", "WARN", "WARNING", "INFO", "DEBUG"}


class WindowLogMessageHandler(logging.Handler):
    """A logging handler that will send log records to an LSP client as
    ``window/logMessage`` notifications."""

    def __init__(
        self,
        server: server.EsbonioLanguageServer,
    ):
        super().__init__()
        self.server = server

    def emit(self, record: logging.LogRecord) -> None:
        """Sends the record to the client."""

        # To avoid infinite recursions, we can't process records coming from pygls.
        if "pygls" in record.name:
            return

        log = self.format(record).strip()
        self.server.show_message_log(log)


@attrs.define
class LoggerConfiguration:
    """Configuration options for a given logger."""

    level: Optional[str] = attrs.field(default=None)
    """The logging level to use, if not set the default logging level will be used."""

    format: Optional[str] = attrs.field(default=None)
    """The log format to use, if not set the default logging level will be used."""

    filepath: Optional[str] = attrs.field(default=None)
    """If set log to a file"""

    stderr: Optional[bool] = attrs.field(default=None)
    """If True, log to stderr, if not set the default value will be used."""

    window: Optional[bool] = attrs.field(default=None)
    """If True, send message as a ``window/logMessage`` notification, if not set the
    default value will be used"""


class LoggingConfigBuilder:
    """Helper class for converting the user's config into the logging config."""

    def __init__(self):
        self.formatters = {}
        self.handlers = {}
        self.loggers = {}

    def _get_formatter(self, format: str) -> str:
        """Return the name of the formatter with the given format string.

        If no such formatter exists, it will be created.
        """
        for key, config in self.formatters.items():
            if config["format"] == format:
                return key

        key = f"fmt{len(self.formatters) + 1:02d}"
        self.formatters[key] = dict(format=format)
        return key

    def _get_file_handler(self, filepath: str, formatter: str) -> str:
        """Return the name of the handler that will log to the given filepath using the
        given formatter name.

        If no such handler exists, it will be created.
        """
        for key, config in self.handlers.items():
            if config.get("class", None) != "logging.FileHandler":
                continue

            if (
                config.get("formatter", None) == formatter
                and config.get("filename", None) == filepath
            ):
                return key

        key = f"file{len(self.handlers) + 1:02d}"
        self.handlers[key] = {
            "class": "logging.FileHandler",
            "level": "DEBUG",  # this way we can handle logs from loggers at any level
            "formatter": formatter,
            "filename": filepath,
        }

        return key

    def _get_stderr_handler(self, formatter: str) -> str:
        """Return the name of the handler that will log to stderr using the given
        formatter name.

        If no such handler exists, it will be created.
        """
        for key, config in self.handlers.items():
            if config.get("class", None) != "logging.StreamHandler":
                continue

            if config.get("formatter", None) == formatter:
                return key

        key = f"stderr{len(self.handlers) + 1:02d}"
        self.handlers[key] = {
            "class": "logging.StreamHandler",
            "level": "DEBUG",  # this way we can handle logs from loggers at any level
            "formatter": formatter,
            "stream": "ext://sys.stderr",
        }

        return key

    def _get_window_handler(
        self, server: server.EsbonioLanguageServer, formatter: str
    ) -> str:
        """Return the name of the handler that will send messages as
        ``window/logMessage`` notificaitions, using the given formatter name.

        If no such formatter exists, it will be created.
        """
        handler_class = f"{__name__}.WindowLogMessageHandler"

        for key, config in self.handlers.items():
            if config.get("()", None) != handler_class:
                continue

            if config.get("formatter", None) == formatter:
                return key

        key = f"window{len(self.handlers) + 1:02d}"
        self.handlers[key] = {
            "()": handler_class,
            "level": "DEBUG",  # this way we can handle logs from loggers at any level
            "formatter": formatter,
            "server": server,
        }

        return key

    def add_logger(
        self,
        name: str,
        level: str,
        format: str,
        filepath: Optional[str],
        stderr: bool,
        window: Optional[server.EsbonioLanguageServer],
    ):
        """Add a configuration for the given logger

        Parameters
        ----------
        name
           The logger name to add a configuration for

        level
           The level at which to log messages

        format
           The format string to apply to messages

        filepath
           If set, record log messages in the given filepath

        stderr
           If ``True``, print messages from this logger to stderr

        window
           If set, send messages from this logger to the client as
           ``window/logMessage`` notifications via the given server instance
        """
        fmt = self._get_formatter(format)
        handlers = []

        if filepath:
            handlers.append(self._get_file_handler(filepath, fmt))

        if stderr:
            handlers.append(self._get_stderr_handler(fmt))

        if window:
            handlers.append(self._get_window_handler(window, fmt))

        if (level := level.upper()) not in LOG_LEVELS:
            level = "DEBUG"

        self.loggers[name] = dict(level=level, propagate=False, handlers=handlers)

    def finish(self) -> Dict[str, Any]:
        """Return the final configuration."""
        return dict(
            version=1,
            disable_existing_loggers=True,
            formatters=self.formatters,
            handlers=self.handlers,
            loggers=self.loggers,
        )


@attrs.define
class LoggingConfig:
    """Configuration options for server logging."""

    level: str = attrs.field(default="error")
    """The default logging level."""

    format: str = attrs.field(default="[%(name)s] %(message)s")
    """The log format string to use."""

    filepath: Optional[str] = attrs.field(default=None)
    """If set, log to a file by default"""

    stderr: bool = attrs.field(default=True)
    """If set, log to stderr by default"""

    window: bool = attrs.field(default=False)
    """If set, send message as a ``window/logMessage`` notification"""

    config: Dict[str, LoggerConfiguration] = attrs.field(factory=dict)
    """Configuration of individual loggers"""

    show_deprecation_warnings: bool = attrs.field(default=False)
    """Developer flag to enable deprecation warnings."""

    def to_logging_config(self, server: server.EsbonioLanguageServer) -> Dict[str, Any]:
        """Convert the user's config into a config dict that can be passed to the
        ``logging.config.dictConfig()`` function.

        Parameters
        ----------
        server
           The language server instance (required for ``window/logMessages``)
        """

        builder = LoggingConfigBuilder()

        # Ensure that there is at least an esbonio logger and a sphinx logger present in
        # the config.
        if "esbonio" not in self.config:
            builder.add_logger(
                "esbonio",
                self.level,
                self.format,
                filepath=self.filepath,
                stderr=self.stderr,
                window=server if self.window else None,
            )

        if "sphinx" not in self.config:
            builder.add_logger(
                "sphinx",
                "info",
                "%(message)s",
                filepath=self.filepath,
                stderr=self.stderr,
                window=server if self.window else None,
            )

        # Process any custom logger configuration
        for name, logger_config in self.config.items():
            window = (
                logger_config.window
                if logger_config.window is not None
                else self.window
            )
            builder.add_logger(
                name,
                logger_config.level or self.level,
                logger_config.format or self.format,
                filepath=(
                    logger_config.filepath
                    if logger_config.filepath is not None
                    else self.filepath
                ),
                stderr=(
                    logger_config.stderr
                    if logger_config.stderr is not None
                    else self.stderr
                ),
                window=server if window else None,
            )

        return builder.finish()


class LogManager(server.LanguageFeature):
    """Manages the logging setup for the server."""

    def initialized(self, params: types.InitializedParams):
        """Setup logging."""
        self.server.configuration.subscribe(
            "esbonio.logging", LoggingConfig, self.setup_logging
        )

    def setup_logging(self, event: server.ConfigChangeEvent[LoggingConfig]):
        """Setup logging according to the given config.

        Parameters
        ----------
        event
           The configuration change event
        """

        records = []
        if event.previous is None:
            # Messages received during initial startup are cached in a MemoryHandler
            # instance, let's resuce them so they can be replayed against the new config.
            for handler in logging.getLogger().handlers:
                if isinstance(handler, MemoryHandler):
                    records = handler.buffer

        config = event.value.to_logging_config(self.server)
        logging.config.dictConfig(config)

        # Replay any captured messages against the new config.
        for record in records:
            logger = logging.getLogger(record.name)
            if logger.isEnabledFor(record.levelno):
                logger.handle(record)


def dump(obj) -> str:
    """Debug helper function that converts an object to JSON."""

    def default(o):
        if isinstance(o, enum.Enum):
            return o.value

        fields = {}
        for k, v in o.__dict__.items():
            if v is None:
                continue

            # Truncate long strings - but not uris!
            if isinstance(v, str) and not k.lower().endswith("uri"):
                v = textwrap.shorten(v, width=25)

            fields[k] = v

        return fields

    return json.dumps(obj, default=default, indent=2)


def esbonio_setup(server: server.EsbonioLanguageServer):
    manager = LogManager(server)
    server.add_feature(manager)
