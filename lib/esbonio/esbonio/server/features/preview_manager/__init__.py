import asyncio
import logging
from http.server import HTTPServer
from http.server import SimpleHTTPRequestHandler
from typing import Any
from typing import Dict
from typing import Optional
from urllib.parse import urlencode

import attrs

from esbonio.server import EsbonioLanguageServer
from esbonio.server import Uri
from esbonio.server.feature import LanguageFeature
from esbonio.server.features.sphinx_manager import SphinxClient
from esbonio.server.features.sphinx_manager import SphinxManager

from .webview import WebviewServer
from .webview import make_ws_server


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


@attrs.define
class PreviewConfig:
    """Configuration settings for previews."""

    bind: str = attrs.field(default="localhost")
    """The network interface to bind to, defaults to ``localhost``"""

    http_port: int = attrs.field(default=0)
    """The port to host the HTTP server on. If ``0`` a random port number will be
    chosen"""

    ws_port: int = attrs.field(default=0)
    """The port to host the WebSocket server on. If ``0`` a random port number will be
    chosen"""

    show_line_markers: bool = attrs.field(default=False)
    """If set, render the source line markers in the preview"""


class PreviewManager(LanguageFeature):
    """Language feature for managing previews."""

    def __init__(self, server: EsbonioLanguageServer, sphinx: SphinxManager):
        super().__init__(server)
        self.sphinx = sphinx
        self.sphinx.add_listener("build", self.on_build)

        logger = server.logger.getChild("PreviewServer")
        self._request_handler_factory = RequestHandlerFactory(logger)
        self._http_server: Optional[HTTPServer] = None
        self._http_future: Optional[asyncio.Future] = None

        self._ws_server: Optional[WebviewServer] = None
        self._ws_task: Optional[asyncio.Task] = None

    @property
    def preview_active(self) -> bool:
        """Return true if the preview is active.

        i.e. there is a HTTP server hosting the build result."""
        return self._http_server is not None

    @property
    def preview_controllable(self) -> bool:
        """Return true if the preview is controllable.

        i.e. there is a web socket server available to control the webview.
        """
        return self._ws_server is not None

    async def get_preview_config(self) -> PreviewConfig:
        """Return the user's preview server configuration."""
        config = await self.server.get_user_config("esbonio.preview", PreviewConfig)
        if config is None:
            self.logger.info(
                "Unable to obtain preview configuration, proceeding with defaults"
            )
            config = PreviewConfig()

        return config

    async def get_http_server(self, config: PreviewConfig) -> HTTPServer:
        """Return the http server instance hosting the previews.

        This will also handle the creation of the server the first time it is called.
        """
        # TODO: Recreate the server if the configuration changes?
        if self._http_server is not None:
            return self._http_server

        self._http_server = HTTPServer(
            (config.bind, config.http_port), self._request_handler_factory
        )

        loop = asyncio.get_running_loop()
        self._http_future = loop.run_in_executor(
            self.server.thread_pool_executor,
            self._http_server.serve_forever,
        )

        return self._http_server

    async def get_webview_server(self, config: PreviewConfig) -> WebviewServer:
        """Return the websocket server used to communicate with the webview."""

        # TODO: Recreate the server if the configuration changes?
        if self._ws_server is not None:
            return self._ws_server

        logger = self.server.logger.getChild("WebviewServer")
        self._ws_server = make_ws_server(self.server, logger)
        self._ws_task = asyncio.create_task(
            self._ws_server.start_ws(config.bind, config.ws_port)
        )

        # HACK: we need to yield control to the event loop to give the ws_server time to
        #       spin up and allocate a port number.
        await asyncio.sleep(1)

        return self._ws_server

    async def on_build(self, client: SphinxClient, result):
        """Called whenever a sphinx build completes."""

        if self._ws_server is None:
            return

        # Only refresh the view if the project we are previewing was built.
        if client.build_uri != self._request_handler_factory.build_uri:
            return

        self.logger.debug("Refreshing preview")
        self._ws_server.reload()

    async def scroll_view(self, line: int):
        """Scroll the webview to the given line number."""

        if self._ws_server is None:
            return

        self._ws_server.scroll(line)

    async def preview_file(self, params):
        # Always check the fully resolved uri.
        src_uri = Uri.parse(params["uri"]).resolve()
        self.logger.debug("Previewing file: '%s'", src_uri)

        client = await self.sphinx.get_client(src_uri)
        if client is None:
            return None

        if client.builder not in {"html", "dirhtml"}:
            self.logger.error(
                "Previews for the '%s' builder are not currently supported",
                client.builder,
            )
            return None

        if (build_path := client.build_file_map.get(src_uri, None)) is None:
            # Has the project been built yet?
            if len(client.build_file_map) == 0:
                # If not, trigger a build and try again
                await client.build()
                return await self.preview_file(params)

            return None

        config = await self.get_preview_config()
        server = await self.get_http_server(config)
        webview = await self.get_webview_server(config)

        self._request_handler_factory.build_uri = client.build_uri
        query_params: Dict[str, Any] = dict(ws=webview.port)

        if config.show_line_markers:
            query_params["show-markers"] = True

        uri = Uri.create(
            scheme="http",
            authority=f"localhost:{server.server_port}",
            path=build_path,
            query=urlencode(query_params),
        )

        self.logger.info("Preview available at: %s", uri.as_string(encode=False))
        return {"uri": uri.as_string(encode=False)}


def esbonio_setup(server: EsbonioLanguageServer, sphinx: SphinxManager):
    manager = PreviewManager(server, sphinx)
    server.add_feature(manager)

    @server.feature("view/scroll")
    async def on_scroll(ls: EsbonioLanguageServer, params):
        await manager.scroll_view(params.line)

    @server.command("esbonio.server.previewFile")
    async def preview_file(ls: EsbonioLanguageServer, *args):
        return await manager.preview_file(args[0][0])
