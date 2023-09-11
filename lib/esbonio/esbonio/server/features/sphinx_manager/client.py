from typing import Dict
from typing import List
from typing import Optional
from typing import Protocol

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
    def builder(self) -> Optional[str]:
        """The name of the Sphinx builder."""

    @property
    def building(self) -> bool:
        """Indicates if the Sphinx instance is building."""

    @property
    def build_uri(self) -> Optional[Uri]:
        """The URI to the Sphinx application's build dir."""

    @property
    def build_file_map(self) -> Dict[Uri, str]:
        """A mapping of source file uris to the corresponding build path that contains
        their content.

        Example
        -------
        >>> client.build_file_map
        {
           Uri(scheme='file', path='/path/to/index.rst'): "index.html",
        }
        """
        ...

    @property
    def diagnostics(self) -> Dict[Uri, List[types.Diagnostic]]:
        """A mapping of source file uris to any diagnostic items."""
        ...

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

    async def stop(self):
        """Stop the client."""
