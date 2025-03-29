from __future__ import annotations

from typing import Literal

import attrs

SyncScrollOptions = Literal[
    "bothWays", "editorWithPreview", "previewWithEditor", "disabled"
]


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

    synchronize_scroll: SyncScrollOptions = attrs.field(default="bothWays")
    """Control how synchronised scrolling works"""

    show_line_markers: bool = attrs.field(default=False)
    """If set, render the source line markers in the preview"""
