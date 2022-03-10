import logging
from functools import partial
from http.server import HTTPServer
from http.server import SimpleHTTPRequestHandler
from typing import Any
from typing import Type

try:
    from http.server import ThreadingHTTPServer

    ServerClass: Type[HTTPServer] = ThreadingHTTPServer
except ImportError:
    # ThreadingHTTPServer is only availble in Python 3.7+
    ServerClass = HTTPServer

logger = logging.getLogger(__name__)


class RequestHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return logger.debug(format, *args)


def make_preview_server(directory: str) -> HTTPServer:
    """Construst a http server that can be used to preview the docs."""
    handler_class = partial(RequestHandler, directory=directory)
    return ServerClass(("localhost", 0), handler_class)
