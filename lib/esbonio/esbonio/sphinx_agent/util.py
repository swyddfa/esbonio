import dataclasses
import json
import logging
import sys
from typing import Any
from typing import Union

logger = logging.getLogger("esbonio.sphinx_agent")


def format_message(data: Any) -> str:
    if dataclasses.is_dataclass(data):
        data = dataclasses.asdict(data)

    content = json.dumps(data)
    content_length = len(content)

    return f"Content-Length: {content_length}\r\n\r\n{content}"


def send_error(id: Union[str, int], code: int, message: str, data=None):
    send_message(
        dict(
            id=id,
            jsonrpc="2.0",
            error=dict(code=code, message=message, data=data),
        )
    )


def send_message(data: Any):
    content = format_message(data).encode("utf8")
    sys.stdout.buffer.write(content)
    sys.stdout.flush()
