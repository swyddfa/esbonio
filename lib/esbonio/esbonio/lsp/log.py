import logging
import typing
from typing import List

from pygls.server import LanguageServer

if typing.TYPE_CHECKING:
    from .rst import ServerConfig


LOG_NAMESPACE = "esbonio.lsp"
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


class MemoryHandler(logging.Handler):
    """A log filter that caches messages in memory."""

    def __init__(self):
        super().__init__()
        self.records: List[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


class LspHandler(logging.Handler):
    """A logging handler that will send log records to an LSP client."""

    def __init__(self, server: LanguageServer):
        super().__init__()
        self.server = server

    def emit(self, record: logging.LogRecord) -> None:
        """Sends the record to the client."""

        # To avoid infinite recursions, it's simpler to just ignore all log records
        # coming from pygls...
        if "pygls" in record.name:
            return

        log = self.format(record).strip()
        self.server.show_message_log(log)


def setup_logging(server: LanguageServer, config: "ServerConfig"):
    """Setup logging to route log messages to the language client as
    ``window/logMessage`` messages.

    Parameters
    ----------
    server
       The server to use to send messages

    config
       The configuration to use
    """

    level = LOG_LEVELS[config.log_level]

    logger = logging.getLogger(LOG_NAMESPACE)
    logger.setLevel(level)

    lsp_handler = LspHandler(server)
    lsp_handler.setLevel(level)

    if len(config.log_filter) > 0:
        lsp_handler.addFilter(LogFilter(config.log_filter))

    formatter = logging.Formatter("[%(name)s] %(message)s")
    lsp_handler.setFormatter(formatter)

    # Look to see if there are any cached messages we should forward to the client.
    for handler in logger.handlers:
        if not isinstance(handler, MemoryHandler):
            continue

        for record in handler.records:
            if logger.isEnabledFor(record.levelno):
                lsp_handler.emit(record)

        logger.removeHandler(handler)

    logger.addHandler(lsp_handler)
