from typing import Any
from typing import Dict
from typing import Optional
from typing import Set
from urllib.parse import urlencode

from lsprotocol import types
from pygls.capabilities import get_capability

from esbonio import server
from esbonio.server import Uri
from esbonio.server.features.project_manager import ProjectManager
from esbonio.server.features.sphinx_manager import SphinxClient
from esbonio.server.features.sphinx_manager import SphinxManager

from .config import PreviewConfig
from .preview import PreviewServer
from .preview import make_http_server
from .webview import WebviewServer
from .webview import make_ws_server


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
        """The sphinx manager."""

        self.built_clients: Set[str] = set()
        """Keeps track of which clients run a build at least once."""

        self.build_path: Optional[str] = None
        """The filepath we are currently displaying."""

        self.build_uri: Optional[Uri] = None
        """The uri of the build dir we are currently serving from."""

        self.config = PreviewConfig()
        """The current configuration."""

        self.projects = projects
        """The project manager."""

        self.preview: Optional[PreviewServer] = None
        """The http server for serving the built files"""

        self.webview: Optional[WebviewServer] = None
        """The server for controlling the webview."""

    @property
    def supports_show_document(self):
        """Indicates if the client supports the `window/showDocument` request."""
        return get_capability(
            self.server.client_capabilities, "window.show_document.support", False
        )

    def initialized(self, params: types.InitializedParams):
        """Called once the initial handshake between client and server has finished."""
        self.configuration.subscribe(
            "esbonio.preview", PreviewConfig, self.update_configuration
        )

    def shutdown(self, params: None):
        """Called when the client instructs the server to ``shutdown``."""

        if self.preview is not None:
            self.preview.stop()

        if self.webview is not None:
            self.webview.stop()

    @property
    def preview_active(self) -> bool:
        """Return true if the preview is active.

        i.e. there is a HTTP server hosting the build result."""
        return self.preview is not None

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

        # (Re)create the http server
        if self.preview is None:
            self.preview = make_http_server(self.server, config)
            self.preview.build_uri = self.build_uri

        elif (
            config.bind != self.preview.config.bind
            or config.http_port != self.preview.config.http_port
        ):
            self.preview.stop()
            self.preview = make_http_server(self.server, config)
            self.preview.build_uri = self.build_uri

        self.config = config
        self.server.run_task(self.show_preview_uri())

    async def on_build(self, client: SphinxClient, result):
        """Called whenever a sphinx build completes."""
        self.built_clients.add(client.id)

        if self.webview is None or self.preview is None:
            return

        # Only refresh the view if the project we are previewing was built.
        if client.build_uri != self.preview.build_uri:
            return

        self.logger.debug("Refreshing preview")
        self.webview.reload()

    async def scroll_view(self, uri: str, line: int):
        """Scroll the webview to the given line number."""

        if self.webview is None:
            return

        self.webview.scroll(uri, line)

    async def preview_file(self, params, retry=True):
        if self.preview is None:
            return None

        # Always check the fully resolved uri.
        src_uri = Uri.parse(params["uri"]).resolve()
        self.logger.debug("Previewing file: '%s'", src_uri)

        if (client := await self.sphinx.get_client(src_uri)) is None:
            return None

        if (project := self.projects.get_project(src_uri)) is None:
            return None

        if (build_path := await project.get_build_path(src_uri)) is None:
            # The client might not have built the project yet.
            if client.id not in self.built_clients and retry is True:
                # Only retry this once.
                await self.sphinx.trigger_build(src_uri)
                return await self.preview_file(params, retry=False)
            else:
                self.logger.debug(
                    "Unable to preview file '%s', not included in build output.",
                    src_uri,
                )
                return None

        self.build_path = build_path
        self.build_uri = self.preview.build_uri = client.build_uri

        if (uri := await self.show_preview_uri()) is None:
            return None

        return {"uri": uri.as_string(encode=False)}

    async def show_preview_uri(self) -> Optional[Uri]:
        """Show the preview uri in the client using a ``window/showDocument`` request.
        Also return the final uri."""

        if self.webview is None or self.preview is None or self.build_path is None:
            return None

        server = await self.preview
        webview = await self.webview

        query_params: Dict[str, Any] = dict(ws=webview.port)

        if self.config.show_line_markers:
            query_params["show-markers"] = True

        uri = Uri.create(
            scheme="http",
            authority=f"localhost:{server.port}",
            path=self.build_path,
            query=urlencode(query_params),
        )
        self.logger.info("Preview available at: %s", uri.as_string(encode=False))

        if self.supports_show_document:
            result = await self.server.show_document_async(
                types.ShowDocumentParams(
                    uri=uri.as_string(encode=False), external=True, take_focus=False
                )
            )
            self.logger.debug("window/showDocument: %s", result)

        return uri


def esbonio_setup(
    esbonio: server.EsbonioLanguageServer,
    sphinx: SphinxManager,
    projects: ProjectManager,
):
    manager = PreviewManager(esbonio, sphinx, projects)
    esbonio.add_feature(manager)

    @esbonio.feature("view/scroll")
    async def on_scroll(ls: server.EsbonioLanguageServer, params):
        await manager.scroll_view(params.uri, params.line)

    @esbonio.command("esbonio.server.previewFile")
    async def preview_file(ls: server.EsbonioLanguageServer, *args):
        return await manager.preview_file(args[0][0])
