import typing
from typing import Optional

from .domains import Domain
from esbonio.lsp.rst import RstLanguageServer
from esbonio.lsp.sphinx import SphinxLanguageServer

if typing.TYPE_CHECKING:
    from esbonio.lsp.roles import Roles


def esbonio_setup(rst: RstLanguageServer):

    roles = rst.get_feature("roles")  # type: Optional[Roles]

    if roles and isinstance(rst, SphinxLanguageServer):
        roles.add_definition_provider(Domain(rst))
