from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Protocol
from typing import Tuple

import aiosqlite

from esbonio.server import Uri
from esbonio.sphinx_agent import types

from .config import SphinxConfig


class SphinxClient(Protocol):
    """Describes the API language features can use to inspect/manipulate a Sphinx
    application instance."""

    @property
    def id(self) -> Optional[str]:
        """The id of the Sphinx instance."""

    @property
    def db(self) -> Optional[aiosqlite.Connection]:
        """Connection to the associated database."""

    @property
    def builder(self) -> Optional[str]:
        """The name of the Sphinx builder."""

    @property
    def building(self) -> bool:
        """Indicates if the Sphinx instance is building."""

    @property
    def build_uri(self) -> Optional[Uri]:
        """The URI to the Sphinx application's build dir."""

    @property
    def conf_uri(self) -> Optional[Uri]:
        """The URI to the Sphinx application's conf dir."""

    @property
    def src_uri(self) -> Optional[Uri]:
        """The URI to the Sphinx application's src dir."""

    async def start(self, config: SphinxConfig):
        """Start the client."""
        ...

    async def create_application(self, config: SphinxConfig) -> types.SphinxInfo:
        """Create a new Sphinx application instance."""
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

    async def get_diagnostics(self) -> Dict[Uri, List[Dict[str, Any]]]:
        """Get the diagnostics for the project."""
        ...

    async def get_document_symbols(self, src_uri: Uri) -> List[types.Symbol]:
        """Get the symbols for the given file."""
        ...

    async def get_workspace_symbols(
        self, query: str
    ) -> List[Tuple[str, str, int, str, str, str]]:
        """Return all the workspace symbols matching the given query"""
        ...

    async def stop(self):
        """Stop the client."""
