from __future__ import annotations

import asyncio
import logging
import pathlib
import typing
from http.server import HTTPServer
from http.server import SimpleHTTPRequestHandler

from esbonio import server
from esbonio.server import Uri

if typing.TYPE_CHECKING:
    from typing import Any

    from .config import PreviewConfig


class RequestHandler(SimpleHTTPRequestHandler):
    def __init__(
        self, *args, logger: logging.Logger, build_mapping: dict[str, Uri], **kwargs
    ) -> None:
        self.logger = logger
        self.build_mapping = build_mapping
        super().__init__(*args, **kwargs)

    def translate_path(self, path: str) -> str:
        url = Uri.parse(f"http://{path}")
        urlpath = pathlib.Path(url.path[1:] if url.path.startswith("/") else url.path)

        if (build_uri := self.build_mapping.get(urlpath.parts[0])) is not None:
            if (build_dir := build_uri.fs_path) is None:
                return "/this/is/not/a/real/path"

            self.directory = build_dir
            fpath = str(pathlib.Path(*urlpath.parts[1:]))
            result = super().translate_path(fpath)
        else:
            result = "/this/is/not/a/real/path"

        # self.logger.debug("Translate: %r -> %r", path, result)
        return result

    def log_message(self, format: str, *args: Any) -> None:
        self.logger.debug(format, *args)


class RequestHandlerFactory:
    """Class for dynamically producing request handlers.

    ``HTTPServer`` works by taking a "request handler" class and creating an instance of
    it for every request it receives. By making this class callable, we can dynamically
    produce a request handler based on the current situation.
    """

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.build_mapping: dict[str, Uri] = {}

    def __call__(self, *args, **kwargs):
        return RequestHandler(
            *args, logger=self.logger, build_mapping=self.build_mapping, **kwargs
        )


class PreviewServer:
    """The http server that serves the built content."""

    def __init__(self, logger: logging.Logger, config: PreviewConfig, executor: Any):
        self.config = config
        """The current configuration."""

        self.logger = logger.getChild("PreviewServer")
        """The logger instance to use."""

        self._handler_factory = RequestHandlerFactory(self.logger)
        """Factory for producing http request handlers."""

        self._startup_task: asyncio.Task | None = None
        """Task that resolves once the server is ready."""

        self._executor: Any = executor
        """The executor in which to run the http server."""

        self._future: asyncio.Future | None = None
        """The future representing the http server's "task"."""

        self._server: HTTPServer | None = None
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
    def build_mapping(self) -> dict[str, Uri]:
        """A mapping from client id to build directory."""
        return self._handler_factory.build_mapping

    @build_mapping.setter
    def build_mapping(self, value: dict[str, Uri]):
        self._handler_factory.build_mapping = value

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
    return PreviewServer(esbonio.logger, config, esbonio.thread_pool)
