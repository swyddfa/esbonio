from __future__ import annotations

import asyncio
import logging
import socket
import threading
import typing

from lsprotocol import types
from pygls.io_ import run_websocket
from pygls.protocol import JsonRPCProtocol
from pygls.protocol import default_converter
from pygls.server import JsonRPCServer
from websockets.asyncio.server import serve

from esbonio import server

if typing.TYPE_CHECKING:
    from websockets.asyncio.server import Server as WebSocketServer
    from websockets.asyncio.server import ServerConnection as WebSocketConnection

    from .config import PreviewConfig


class WebviewServer(JsonRPCServer):
    """The webview server controlls the webpage hosting the preview.

    Used to implement automatic reloads and features like sync scrolling.
    """

    protocol: JsonRPCProtocol

    def __init__(self, logger: logging.Logger, config: PreviewConfig, *args, **kwargs):
        super().__init__(JsonRPCProtocol, default_converter, *args, **kwargs)

        self.config = config
        self.logger = logger.getChild("WebviewServer")

        self._connected = False
        self._ws_server: WebSocketServer | None = None

        self._startup_task: asyncio.Task | None = None
        """The task that resolves once startup is complete."""

        self._server_task: asyncio.Task | None = None
        """The task hosting the server itself."""

        self._editor_in_control: asyncio.Task | None = None
        """If set, the editor is in control and the view should not emit scroll events"""

        self._view_in_control: asyncio.Task | None = None
        """If set, the view is in control and the editor should not emit scroll events"""

        self._current_uri: str | None = None
        """If set, indicates the current uri the editor and view are scrolling."""

    def __await__(self):
        """Makes the server await-able"""
        if self._startup_task is None:
            self._startup_task = asyncio.create_task(self.start())

        return self._startup_task.__await__()

    @property
    def port(self):
        if self._ws_server is None:
            return None

        sock = list(self._ws_server.sockets)[0]
        return sock.getsockname()[1]

    @property
    def connected(self) -> bool:
        """Indicates when we have an active connection to the client."""
        return self._connected

    def reload(self):
        """Reload the current view."""
        if self.connected:
            self.protocol.notify("view/reload", {})

    def scroll(self, uri: str, line: int):
        """Called by the editor to scroll the current webview."""
        if not self.connected or self._view_in_control:
            return

        if self.config.synchronize_scroll not in {"bothWays", "editorWithPreview"}:
            return

        # If the editor is already in control, reset the cooldown
        if self._editor_in_control:
            self._editor_in_control.cancel()

        self._current_uri = uri
        self._editor_in_control = asyncio.create_task(self.cooldown("editor"))
        self.protocol.notify("view/scroll", {"uri": uri, "line": line})

    async def cooldown(self, name: str):
        """Create a cooldown."""
        await asyncio.sleep(1)

        # Unset the cooldown
        self.logger.debug("%s cooldown ended", name)
        setattr(self, f"_{name}_in_control", None)

    async def start(self):
        """Start the server and wrap the server coroutine in a task."""
        self._server_task = asyncio.create_task(
            self._start_ws(self.config.bind, self.config.ws_port)
        )

        # HACK: we need to yield control to the event loop to give the ws_server time to
        #       spin up and allocate a port number.
        await asyncio.sleep(1)
        return self

    def stop(self):
        """Stop the server."""
        self.logger.debug("Shutting down preview WebSocket server")

        if self._server_task is not None:
            self._server_task.cancel()

    async def _start_ws(self, host: str, port: int) -> None:
        """Actually, start the server."""

        async def connection(websocket: WebSocketConnection):
            self._connected = True
            self.logger.debug("Connected")

            await run_websocket(
                stop_event=threading.Event(),
                websocket=websocket,
                protocol=self.protocol,
                logger=self.logger,
                error_handler=self.report_server_error,
            )

            self.logger.debug("Connection lost")
            self._connected = False

        self._ws_server = await serve(
            connection,
            host,
            port,
            # logger=self.logger.getChild("ws"),
            family=socket.AF_INET,  # Use IPv4 only.
        )
        async with self._ws_server:
            await self._ws_server.serve_forever()


def make_ws_server(
    esbonio: server.EsbonioLanguageServer, config: PreviewConfig
) -> WebviewServer:
    server = WebviewServer(esbonio.logger, config)

    @server.feature("editor/scroll")
    def on_scroll(ls: WebviewServer, params):
        """Called by the webview to scroll the editor."""
        if not server.connected or server._editor_in_control:
            return

        if ls.config.synchronize_scroll not in {"bothWays", "previewWithEditor"}:
            return

        # If the view is already in control, reset the cooldown.
        if server._view_in_control:
            server._view_in_control.cancel()

        server._view_in_control = asyncio.create_task(server.cooldown("view"))

        esbonio.window_show_document(
            types.ShowDocumentParams(
                uri=params.uri,
                external=False,
                selection=types.Range(
                    start=types.Position(line=params.line - 1, character=0),
                    end=types.Position(line=params.line, character=0),
                ),
            )
        )

    return server
