import logging
from typing import List

LOG_NAMESPACE = "esbonio"


class MemoryHandler(logging.Handler):
    """A logging handler that caches messages in memory."""

    def __init__(self):
        super().__init__()
        self.records: List[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)
