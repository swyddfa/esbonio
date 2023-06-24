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

    def feature(self, feature_name: str, options=None):
        return self.lsp.fm.feature(feature_name, options)

    def reload(self):
        """Reload the current view."""
        self.lsp.notify("view/reload", {})

    async def start_ws(self, host: str, port: int) -> None:
        async def connection(websocket):
            loop = asyncio.get_running_loop()
            transport = WebSocketTransportAdapter(websocket, loop)
            self.lsp.connection_made(transport)

            async for message in websocket:
                self.lsp._procedure_handler(
                    json.loads(message, object_hook=self.lsp._deserialize_message)
                )

        async with serve(
            connection,
            host,
            port,
            logger=self.logger.getChild("rpc"),
            family=socket.AF_INET,  # Use IPv4 only.
        ) as ws_server:
            sock = ws_server.sockets[0]
            self.port = sock.getsockname()[1]
            await asyncio.Future()  # run forever


def make_ws_server(logger: logging.Logger):
    server = WebviewServer(logger)
    return server


if __name__ == "__main__":
    logger = logging.getLogger("webview")
    server = make_ws_server(logger)
    asyncio.run(server.start_ws("localhost", 9876))
