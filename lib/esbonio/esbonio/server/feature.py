from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from .server import EsbonioLanguageServer


class LanguageFeature:
    """Base class for language features."""

    def __init__(self, server: EsbonioLanguageServer):
        self.server = server
        self.logger = server.logger.getChild(self.__class__.__name__)
