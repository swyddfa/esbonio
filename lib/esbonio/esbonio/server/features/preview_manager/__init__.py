import asyncio
import logging
import sys
from http.server import HTTPServer
from http.server import SimpleHTTPRequestHandler
from typing import Any
from typing import Dict
from typing import Optional
from urllib.parse import urlencode

from lsprotocol import types

from esbonio import server
from esbonio.server import Uri
from esbonio.server.features.project_manager import ProjectManager
from esbonio.server.features.sphinx_manager import SphinxClient
from esbonio.server.features.sphinx_manager import SphinxManager

from .config import PreviewConfig
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
class PreviewManager(server.LanguageFeature):
    """Language feature for managing previews."""

    def __init__(
        self,
        server: server.EsbonioLanguageServer,
        sphinx: SphinxManager,
        projects: ProjectManager,
    ):
        super().__init__(server)
        self.sphinx = sphinx
        self.sphinx.add_listener("build", self.on_build)

        self.projects = projects
        self.config = PreviewConfig()

        logger = server.logger.getChild("PreviewServer")
        self._request_handler_factory = RequestHandlerFactory(logger)
        self._http_server: Optional[HTTPServer] = None
        self._http_future: Optional[asyncio.Future] = None

        self.webview: Optional[WebviewServer] = None
        """The server for controlling the webview."""

    def initialized(self, params: types.InitializedParams):
        """Called once the initial handshake between client and server has finished."""
        self.configuration.subscribe(
            "esbonio.preview", PreviewConfig, self.update_configuration
        )

    def shutdown(self, params: None):
        """Called when the client instructs the server to ``shutdown``."""
        args = {}
        if sys.version_info.minor > 8:
            args["msg"] = "Server is shutting down."

        if self._http_server:
            self.logger.debug("Shutting down preview HTTP server")
            self._http_server.shutdown()

        if self.webview is not None:
            self.webview.stop()

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
        return self.webview is not None

    def update_configuration(self, event: server.ConfigChangeEvent[PreviewConfig]):
        """Called when the user's configuration is updated."""
        config = event.value

        # (Re)create the websocket server
        if self.webview is None:
            self.webview = make_ws_server(self.server, config)

        elif (
            config.bind != self.webview.config.bind
            or config.ws_port != self.webview.config.ws_port
        ):
            self.webview.stop()
            self.webview = make_ws_server(self.server, config)

        self.config = config

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

    async def on_build(self, client: SphinxClient, result):
        """Called whenever a sphinx build completes."""

        if self.webview is None:
            return

        # Only refresh the view if the project we are previewing was built.
        if client.build_uri != self._request_handler_factory.build_uri:
            return

        self.logger.debug("Refreshing preview")
        self.webview.reload()

    async def scroll_view(self, line: int):
        """Scroll the webview to the given line number."""

        if self.webview is None:
            return

        self.webview.scroll(line)

    async def preview_file(self, params):
        # Always check the fully resolved uri.
        if self.webview is None:
            return None

        src_uri = Uri.parse(params["uri"]).resolve()
        self.logger.debug("Previewing file: '%s'", src_uri)

        if (client := await self.sphinx.get_client(src_uri)) is None:
            return None

        if (project := self.projects.get_project(src_uri)) is None:
            return None

        if (build_path := await project.get_build_path(src_uri)) is None:
            self.logger.debug(
                "Unable to preview file '%s', not included in build output.", src_uri
            )
            return None

        server = await self.get_http_server(self.config)
        webview = await self.webview

        self._request_handler_factory.build_uri = client.build_uri
        query_params: Dict[str, Any] = dict(ws=webview.port)

        if self.config.show_line_markers:
            query_params["show-markers"] = True

        uri = Uri.create(
            scheme="http",
            authority=f"localhost:{server.server_port}",
            path=build_path,
            query=urlencode(query_params),
        )

        self.logger.info("Preview available at: %s", uri.as_string(encode=False))
        return {"uri": uri.as_string(encode=False)}


def esbonio_setup(
    esbonio: server.EsbonioLanguageServer,
    sphinx: SphinxManager,
    projects: ProjectManager,
):
    manager = PreviewManager(esbonio, sphinx, projects)
    esbonio.add_feature(manager)

    @esbonio.feature("view/scroll")
    async def on_scroll(ls: server.EsbonioLanguageServer, params):
        await manager.scroll_view(params.line)

    @esbonio.command("esbonio.server.previewFile")
    async def preview_file(ls: server.EsbonioLanguageServer, *args):
        return await manager.preview_file(args[0][0])
