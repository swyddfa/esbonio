from __future__ import annotations

import enum
import typing
from typing import Protocol

if typing.TYPE_CHECKING:
    import pathlib
    from typing import Any
    from typing import Dict
    from typing import Generator
    from typing import List
    from typing import Optional

    from esbonio.server import Uri
    from esbonio.sphinx_agent import types


class ClientState(enum.Enum):
    """The set of possible states the client may be in."""

    Starting = enum.auto()
    """The client is starting."""

    Restarting = enum.auto()
    """The client is restarting."""

    Running = enum.auto()
    """The client is running normally."""

    Building = enum.auto()
    """The client is currently building."""

    Errored = enum.auto()
    """The client has enountered some unrecoverable error and should not be used."""

    Exited = enum.auto()
    """The client is no longer running."""


class SphinxClient(Protocol):
    """Describes the API language features can use to inspect/manipulate a Sphinx
    application instance."""

    state: Optional[ClientState]
    sphinx_info: Optional[types.SphinxInfo]

    @property
    def id(self) -> str:
        """The id of the Sphinx instance."""
        ...

    @property
    def db(self) -> pathlib.Path:
        """Connection to the associated database."""

    @property
    def builder(self) -> str:
        """The name of the Sphinx builder."""
        ...

    @property
    def build_uri(self) -> Uri:
        """The URI to the Sphinx application's build dir."""
        ...

    @property
    def conf_uri(self) -> Uri:
        """The URI to the Sphinx application's conf dir."""
        ...

    @property
    def src_uri(self) -> Uri:
        """The URI to the Sphinx application's src dir."""
        ...

    def __await__(self) -> Generator[Any, None, SphinxClient]:
        """A SphinxClient should be awaitable"""
        ...

    def add_listener(self, event: str, handler): ...

    async def start(self) -> SphinxClient:
        """Start the client."""
        ...

    async def restart(self) -> SphinxClient:
        """Restart the client."""
        ...

    async def build(
        self,
        *,
        filenames: Optional[List[str]] = None,
        force_all: bool = False,
        content_overrides: Optional[Dict[str, str]] = None,
    ) -> types.BuildResult:
        """Trigger a Sphinx build."""
        ...

    async def stop(self):
        """Stop the client."""
