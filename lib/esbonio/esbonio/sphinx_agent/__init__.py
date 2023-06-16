"""This module implements the Sphinx agent.

It wraps a Sphinx application object, allowing the main language server process to
interact with it.

Whereas the language server originally had to be installed within the same Python
environment as Sphinx, the agent allows the server to run in a completely separate
Python environment and still gather the information it needs.

This is possible by taking advantage of the ``PYTHONPATH`` environment variable, using
it to expose *just this module* to the Python environment hosting Sphinx. To prevent
a potential clash of dependencies, this module is written with only what is available
in the stdlib and Sphinx itself.

Unfortunately, this does mean re-inventing some wheels, but hopefully what we gain in
portability makes it worth the trade off.
"""
import asyncio
import dataclasses
import json
import logging
import re
import sys
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import Dict
from typing import Type
from typing import TypeVar

from .handlers import HANDLERS
from .util import send_error

logger = logging.getLogger(__name__)


T = TypeVar("T")


def parse_message(obj: Dict, cls: Type[T]) -> T:
    """Convert a raw dict into the given type"""

    if dataclasses.is_dataclass(cls):
        kwargs = {}
        fields = {f.name: f for f in dataclasses.fields(cls)}

        for key, value in obj.items():
            kwargs[key] = parse_message(value, fields[key].type)

        return cls(**kwargs)

    return obj


def handle_message(data: bytes):
    message = json.loads(data.decode("utf8"))

    method = message.get("method", None)
    if not method:
        raise TypeError("Invalid message")

    type_, handler = HANDLERS.get(method, (None, None))
    if type_ is None or handler is None:
        raise TypeError(f"Unknown method: '{method}'")

    obj = parse_message(message, type_)
    try:
        handler(obj)
    except Exception as e:
        msg_id = message.get("id", None)
        if msg_id is not None:
            send_error(
                id=msg_id,
                code=-32602,
                message=f"{e}",
                data=dict(traceback=traceback.format_exc()),
            )


async def main_loop(loop, executor, stop_event, rfile, proxy):
    """Originally taken from ``pygls``"""

    CONTENT_LENGTH_PATTERN = re.compile(rb"^Content-Length: (\d+)\r\n$")

    # Initialize message buffer
    content_length = 0

    while not stop_event.is_set() and not rfile.closed:
        # Read a header line
        header = await loop.run_in_executor(executor, rfile.readline)
        if not header:
            break

        # Extract content length if possible
        if not content_length:
            match = CONTENT_LENGTH_PATTERN.fullmatch(header)
            if match:
                content_length = int(match.group(1))
                logger.debug("Content length: %s", content_length)

        # Check if all headers have been read (as indicated by an empty line \r\n)
        if content_length and not header.strip():
            # Read body
            body = await loop.run_in_executor(executor, rfile.read, content_length)
            if not body:
                break

            proxy(body)

            # Reset the buffer
            content_length = 0


async def main():
    loop = asyncio.get_running_loop()
    event = threading.Event()
    executor = ThreadPoolExecutor(max_workers=2)

    await main_loop(loop, executor, event, sys.stdin.buffer, handle_message)
