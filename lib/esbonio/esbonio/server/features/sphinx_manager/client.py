from __future__ import annotations

import enum
import typing
from typing import Protocol

if typing.TYPE_CHECKING:
    from typing import Any
    from typing import Dict
    from typing import Generator
    from typing import List
    from typing import Optional
    from typing import Tuple

    import aiosqlite

    from esbonio.server import Uri
    from esbonio.sphinx_agent import types


class ClientState(enum.Enum):
    """The set of possible states the client may be in."""

    Starting = enum.auto()
    """The client is starting."""

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
    def db(self) -> Optional[aiosqlite.Connection]:
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

    async def build(
        self,
        *,
        filenames: Optional[List[str]] = None,
        force_all: bool = False,
        content_overrides: Optional[Dict[str, str]] = None,
    ) -> types.BuildResult:
        """Trigger a Sphinx build."""
        ...

    async def get_src_uris(self) -> List[Uri]:
        """Return all known source files."""
        ...

    async def get_build_path(self, src_uri: Uri) -> Optional[str]:
        """Get the build path associated with the given ``src_uri``."""

    async def get_config_value(self, name: str) -> Optional[Any]:
        """Return the requested configuration value, if available."""

    async def get_diagnostics(self) -> Dict[Uri, List[Dict[str, Any]]]:
        """Get the diagnostics for the project."""
        ...

    async def get_directives(self) -> List[Tuple[str, Optional[str]]]:
        """Get all the directives known to Sphinx."""
        ...

    async def get_document_symbols(self, src_uri: Uri) -> List[types.Symbol]:
        """Get the symbols for the given file."""
        ...

    async def find_symbols(self, **kwargs) -> List[types.Symbol]:
        """Find symbols which match the given criteria."""
        ...

    async def get_workspace_symbols(
        self, query: str
    ) -> List[Tuple[str, str, int, str, str, str]]:
        """Return all the workspace symbols matching the given query string"""
        ...

    async def stop(self):
        """Stop the client."""
