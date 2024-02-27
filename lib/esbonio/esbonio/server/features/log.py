import enum
import json
import logging
import textwrap
from typing import List

import attrs
from lsprotocol import types

from esbonio import server

LOG_LEVELS = {
    "debug": logging.DEBUG,
    "error": logging.ERROR,
    "info": logging.INFO,
}




class LogFilter(logging.Filter):
    """A log filter that accepts message from any of the listed logger names."""

    def __init__(self, names):
        self.names = names

    def filter(self, record):
        return any(record.name == name for name in self.names)


class LspHandler(logging.Handler):
    """A logging handler that will send log records to an LSP client."""

    def __init__(
        self,
        server: server.EsbonioLanguageServer,
        show_deprecation_warnings: bool = False,
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
class ServerLogConfig:
    """Configuration options for server logging."""

    log_filter: List[str] = attrs.field(factory=list)
    """A list of logger names to restrict output to."""

    log_level: str = attrs.field(default="error")
    """The logging level of server messages to display."""

    show_deprecation_warnings: bool = attrs.field(default=False)
    """Developer flag to enable deprecation warnings."""


class LogManager(server.LanguageFeature):
    """Manages the logging setup for the server."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def initialized(self, params: types.InitializedParams):
        """Setup logging."""
        self.server.configuration.subscribe(
            "esbonio.server", ServerLogConfig, self.setup_logging
        )

    def setup_logging(self, event: server.ConfigChangeEvent[ServerLogConfig]):
        """Setup logging to route log messages to the language client as
        ``window/logMessage`` messages.

        Parameters
        ----------
        previous
           The previous configuration value

        config
           The configuration to use
        """
        config = event.value
        level = LOG_LEVELS[config.log_level]

        # warnlog = logging.getLogger("py.warnings")
        logger = logging.getLogger(server.LOG_NAMESPACE)
        logger.setLevel(level)

        lsp_handler = LspHandler(self.server, config.show_deprecation_warnings)
        lsp_handler.setLevel(level)

        if len(config.log_filter) > 0:
            lsp_handler.addFilter(LogFilter(config.log_filter))

        formatter = logging.Formatter("[%(name)s] %(message)s")
        lsp_handler.setFormatter(formatter)

        # Look to see if there are any cached messages we should forward to the client.
        for handler in logger.handlers:
            # Remove any previous instances of the LspHandler
            if isinstance(handler, LspHandler):
                logger.removeHandler(handler)

            # Forward any cached messages to the client
            if isinstance(handler, server.MemoryHandler):
                for record in handler.records:
                    if logger.isEnabledFor(record.levelno):
                        lsp_handler.emit(record)

                logger.removeHandler(handler)

        logger.addHandler(lsp_handler)
        # warnlog.addHandler(lsp_handler)


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
