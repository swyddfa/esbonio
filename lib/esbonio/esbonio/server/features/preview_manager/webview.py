"""This module implements the websocket server used to communicate with preivew
 windows."""
import asyncio
import json
import logging
import socket

from pygls.protocol import JsonRPCProtocol
from pygls.protocol import default_converter
from pygls.server import Server
from pygls.server import WebSocketTransportAdapter
from websockets.server import serve

from esbonio.server import EsbonioLanguageServer


class WebviewServer(Server):
    """The webview server controlls the webpage hosting the preview.

    Used to implement automatic reloads and features like sync scrolling.
    """

    lsp: JsonRPCProtocol

    def __init__(self, logger: logging.Logger, *args, **kwargs):
        super().__init__(JsonRPCProtocol, default_converter, *args, **kwargs)
        self.logger = logger
        self.lsp._send_only_body = True
        self.port = None

        self._connected = False
    @property
    def connected(self) -> bool:
        """Indicates when we have an active connection to the client."""
        return self._connected

    def feature(self, feature_name: str, options=None):
        return self.lsp.fm.feature(feature_name, options)

    def reload(self):
        """Reload the current view."""
        if self.connected:
            self.lsp.notify("view/reload", {})

    def scroll(self, line: int):
        """Scroll the current view."""
        if self.lsp.transport:
            self.lsp.notify("view/scroll", {"line": line})

    async def start_ws(self, host: str, port: int) -> None:  # type: ignore[override]
        """Start the server."""

        async def connection(websocket):
            loop = asyncio.get_running_loop()
            transport = WebSocketTransportAdapter(websocket, loop)

            self.lsp.connection_made(transport)  # type: ignore[arg-type]
            self._connected = True
            self.logger.debug("Connected")

            async for message in websocket:
                self.lsp._procedure_handler(
                    json.loads(message, object_hook=self.lsp._deserialize_message)
                )

            self.logger.debug("Connection lost")
            self._connected = False

        async with serve(
            connection,
            host,
            port,
            # logger=self.logger.getChild("ws"),
            family=socket.AF_INET,  # Use IPv4 only.
        ) as ws_server:
            sock = list(ws_server.sockets)[0]
            self.port = sock.getsockname()[1]
            await asyncio.Future()  # run forever


def make_ws_server(
    esbonio: EsbonioLanguageServer, logger: logging.Logger
) -> WebviewServer:
    server = WebviewServer(logger)

    @server.feature("editor/scroll")
    def on_scroll(ls: WebviewServer, params):
        esbonio.lsp.notify("editor/scroll", dict(line=params.line))

    return server
