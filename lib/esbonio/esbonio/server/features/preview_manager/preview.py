from __future__ import annotations

import asyncio
import logging
import typing
from http.server import HTTPServer
from http.server import SimpleHTTPRequestHandler

from esbonio import server
from esbonio.server import Uri

if typing.TYPE_CHECKING:
    from typing import Any
    from typing import Optional

    from .config import PreviewConfig


class RequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, logger: logging.Logger, directory: str, **kwargs) -> None:
        self.logger = logger
        super().__init__(*args, directory=directory, **kwargs)

    def translate_path(self, path: str) -> str:
        result = super().translate_path(path)
        # self.logger.debug("Translate: '%s' -> '%s'", path, result)
        return result

    def log_message(self, format: str, *args: Any) -> None:
        self.logger.debug(format, *args)


class RequestHandlerFactory:
    """Class for dynamically producing request handlers.

    ``HTTPServer`` works by taking a "request handler" class and creating an instance of
    it for every request it receives. By making this class callable, we can dynamically
    produce a request handler based on the current situation.
    """

    def __init__(self, logger: logging.Logger, build_uri: Optional[Uri] = None):
        self.logger = logger
        self.build_uri = build_uri

    def __call__(self, *args, **kwargs):
        if self.build_uri is None:
            raise ValueError("No build directory set")

        if (build_dir := self.build_uri.fs_path) is None:
            raise ValueError(
                "Unable to determine build dir from uri: '%s'", self.build_uri
            )

        return RequestHandler(*args, logger=self.logger, directory=build_dir, **kwargs)


class PreviewServer:
    """The http server that serves the built content."""

    def __init__(self, logger: logging.Logger, config: PreviewConfig, executor: Any):
        self.config = config
        """The current configuration."""

        self.logger = logger.getChild("PreviewServer")
        """The logger instance to use."""

        self._handler_factory = RequestHandlerFactory(self.logger)
        """Factory for producing http request handlers."""

        self._startup_task: Optional[asyncio.Task] = None
        """Task that resolves once the server is ready."""

        self._executor: Any = executor
        """The executor in which to run the http server."""

        self._future: Optional[asyncio.Future] = None
        """The future representing the http server's "task"."""

        self._server: Optional[HTTPServer] = None
        """The http server itself."""

    def __await__(self):
        """Makes the server await-able"""
        if self._startup_task is None:
            self._startup_task = asyncio.create_task(self.start())

        return self._startup_task.__await__()

    @property
    def port(self):
        if self._server is None:
            return 0

        return self._server.server_port

    @property
    def build_uri(self):
        return self._handler_factory.build_uri

    @build_uri.setter
    def build_uri(self, value):
        self._handler_factory.build_uri = value

    async def start(self):
        """Start the server."""

        # Yes, this method does not need to be async. However, making it async means it
        # aligns well with the pattern we've established in other components.

        self._server = HTTPServer(
            (self.config.bind, self.config.http_port), self._handler_factory
        )

        loop = asyncio.get_running_loop()
        self._future = loop.run_in_executor(self._executor, self._server.serve_forever)

        return self

    def stop(self):
        """Stop the server."""
        if self._server is not None:
            self.logger.debug("Shutting down preview HTTP server")
            self._server.shutdown()

        if self._future is not None:
            self.logger.debug("Cancelling HTTP future: %s", self._future.cancel())


def make_http_server(
    esbonio: server.EsbonioLanguageServer, config: PreviewConfig
) -> PreviewServer:
    return PreviewServer(esbonio.logger, config, esbonio.thread_pool_executor)
