import dataclasses
import json
import logging
import pathlib
import sys
from typing import Any
from typing import Union

from sphinx.locale import _TranslationProxy

logger = logging.getLogger("esbonio.sphinx_agent")


def _serialize_message(obj):
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)

    if isinstance(obj, (_TranslationProxy, pathlib.Path)):
        return str(obj)

    if isinstance(obj, set):
        return list(obj)

    return obj


def as_json(data: Any) -> str:
    return json.dumps(data, default=_serialize_message)


def format_message(data: Any) -> str:
    content = as_json(data)
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
