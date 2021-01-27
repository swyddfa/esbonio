"""This module defines a custom logging handler that publishes log messages to an LSP
client."""

import logging

from pygls.server import LanguageServer


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
