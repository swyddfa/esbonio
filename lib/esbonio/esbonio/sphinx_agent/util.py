import dataclasses
import json
import logging
import sys
from typing import Any

logger = logging.getLogger("esbonio.sphinx_agent")


def format_message(data: Any) -> str:
    if dataclasses.is_dataclass(data):
        data = dataclasses.asdict(data)

    content = json.dumps(data)
    content_length = len(content)

    return f"Content-Length: {content_length}\r\n\r\n{content}"


def send_message(data: Any):
    content = format_message(data).encode("utf8")
    sys.stdout.buffer.write(content)
    sys.stdout.flush()
