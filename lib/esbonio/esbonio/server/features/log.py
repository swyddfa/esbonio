import enum
import json
import logging
import pathlib
import re
import textwrap
import traceback
from typing import List
from typing import Tuple

import attrs
from lsprotocol import types

from esbonio import server
from esbonio.server import Uri

LOG_LEVELS = {
    "debug": logging.DEBUG,
    "error": logging.ERROR,
    "info": logging.INFO,
}


# e.g. /.../filename.rst:54: (ERROR/3) Unexpected indentation.
#      c:\...\filename.rst:54: (ERROR/3) Unexpected indentation.
DOCUTILS_ERROR = re.compile(
    r"""
    ^\s*(?P<filepath>.+?):
    (?P<linum>\d+):
    \s*\((?P<levelname>\w+)/(?P<levelnum>\d)\)
    (?P<message>.*)$
    """,
    re.VERBOSE,
)

DOCUTILS_SEVERITY = {
    0: types.DiagnosticSeverity.Hint,
    1: types.DiagnosticSeverity.Information,
    2: types.DiagnosticSeverity.Warning,
    3: types.DiagnosticSeverity.Error,
    4: types.DiagnosticSeverity.Error,
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
            tags.append(types.DiagnosticTag.Deprecated)

        diagnostic = types.Diagnostic(
            range=types.Range(
                start=types.Position(line=line - 1, character=0),
                end=types.Position(line=line, character=0),
            ),
            message=message,
            severity=types.DiagnosticSeverity.Warning,
            tags=tags,
        )

        self.server.add_diagnostics("esbonio", Uri.for_file(path), diagnostic)
        self.server.sync_diagnostics()

    def handle_diagnostic(self, record: logging.LogRecord):
        """Look for any diagnostics to report in the log message."""

        if (match := DOCUTILS_ERROR.match(record.msg)) is not None:
            uri = Uri.for_file(match.group("filepath"))
            line = int(match.group("linum"))
            severity = int(match.group("levelnum"))

            diagnostic = types.Diagnostic(
                message=match.group("message").strip(),
                severity=DOCUTILS_SEVERITY.get(severity),
                range=types.Range(
                    start=types.Position(line=line - 1, character=0),
                    end=types.Position(line=line, character=0),
                ),
            )
            self.server.add_diagnostics("docutils", uri, diagnostic)

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
        else:
            self.handle_diagnostic(record)

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
