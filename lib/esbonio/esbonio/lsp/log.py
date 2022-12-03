import logging
import pathlib
import traceback
import typing
from typing import List
from typing import Tuple

import pygls.uris as uri
from pygls.lsp.types import Diagnostic
from pygls.lsp.types import DiagnosticSeverity
from pygls.lsp.types import DiagnosticTag
from pygls.lsp.types import Position
from pygls.lsp.types import Range

if typing.TYPE_CHECKING:
    from .rst import RstLanguageServer
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
    """A logging handler that caches messages in memory."""

    def __init__(self):
        super().__init__()
        self.records: List[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


class LspHandler(logging.Handler):
    """A logging handler that will send log records to an LSP client."""

    def __init__(
        self, server: "RstLanguageServer", show_deprecation_warnings: bool = False
    ):
        super().__init__()
        self.server = server
        self.show_deprecation_warnings = show_deprecation_warnings

    def get_warning_path(self, warning: str) -> Tuple[str, List[str]]:
        """Determine the filepath that the warning was emitted from."""

        path, *parts = warning.split(":")

        # On windows the rest of the path will be in the first element of parts.
        if pathlib.Path(warning).drive:
            path += f":{parts.pop(0)}"

        return path, parts

    def handle_warning(self, record: logging.LogRecord):
        """Publish warnings to the client as diagnostics."""

        if not isinstance(record.args, tuple):
            self.server.logger.debug(
                "Unable to handle warning, expected tuple got: %s", record.args
            )
            return

        # The way warnings are logged is different in Python 3.11+
        if len(record.args) == 0:
            argument = record.msg
        else:
            argument = record.args[0]  # type: ignore

        if not isinstance(argument, str):
            self.server.logger.debug(
                "Unable to handle warning, expected string got: %s", argument
            )
            return

        warning, *_ = argument.split("\n")
        path, (linenum, category, *msg) = self.get_warning_path(warning)

        category = category.strip()
        message = ":".join(msg).strip()

        try:
            line = int(linenum)
        except ValueError:
            line = 1
            self.server.logger.debug(
                "Unable to parse line number: '%s'\n%s", linenum, traceback.format_exc()
            )

        tags = []
        if category == "DeprecationWarning":
            tags.append(DiagnosticTag.Deprecated)

        diagnostic = Diagnostic(
            range=Range(
                start=Position(line=line - 1, character=0),
                end=Position(line=line, character=0),
            ),
            message=message,
            severity=DiagnosticSeverity.Warning,
            tags=tags,
        )

        self.server.add_diagnostics("esbonio", uri.from_fs_path(path), diagnostic)
        self.server.sync_diagnostics()

    def emit(self, record: logging.LogRecord) -> None:
        """Sends the record to the client."""

        # To avoid infinite recursions, it's simpler to just ignore all log records
        # coming from pygls...
        if "pygls" in record.name:
            return

        if record.name == "py.warnings":
            if not self.show_deprecation_warnings:
                return

            self.handle_warning(record)

        log = self.format(record).strip()
        self.server.show_message_log(log)


def setup_logging(server: "RstLanguageServer", config: "ServerConfig"):
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

    warnlog = logging.getLogger("py.warnings")
    logger = logging.getLogger(LOG_NAMESPACE)
    logger.setLevel(level)

    lsp_handler = LspHandler(server, config.show_deprecation_warnings)
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
    warnlog.addHandler(lsp_handler)
