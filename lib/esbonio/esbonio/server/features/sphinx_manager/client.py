from typing import Optional
from typing import Protocol

from esbonio.server import Uri
from esbonio.sphinx_agent import types

from .config import SphinxConfig


class SphinxClient(Protocol):
    """Describes the API language features can use to inspect/manipulate a Sphinx
    application instance."""

    @property
    def builder(self) -> Optional[str]:
        """The name of the Sphinx builder."""

    @property
    def build_uri(self) -> Optional[Uri]:
        """The URI to the Sphinx applicaiton's build dir."""

    @property
    def conf_uri(self) -> Optional[Uri]:
        """The URI to the Sphinx application's conf dir."""

    @property
    def src_uri(self) -> Optional[Uri]:
        """The URI to the Sphinx application's src dir."""

    async def create_application(self, config: SphinxConfig) -> types.SphinxInfo:
        """Create a new Sphinx application instance."""
        ...

    async def build(self):
        """Trigger a Sphinx build."""

    async def stop(self):
        """Stop the client."""
