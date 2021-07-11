import typing

from .domains import Domain
from .filepaths import Filepath
from esbonio.lsp.rst import RstLanguageServer
from esbonio.lsp.sphinx import SphinxLanguageServer

if typing.TYPE_CHECKING:
    from typing import Optional
    from esbonio.lsp.roles import Roles
    from esbonio.lsp.directives import Directives


def esbonio_setup(rst: RstLanguageServer):

    roles = rst.get_feature("roles")  # type: Optional[Roles]
    directives = rst.get_feature("directives")  # type: Optional[Directives]

    filepaths = Filepath(rst)

    if roles and isinstance(rst, SphinxLanguageServer):
        roles.add_target_provider(Domain(rst))
        roles.add_target_provider(filepaths)

    if directives and isinstance(rst, SphinxLanguageServer):
        directives.add_argument_provider(filepaths)
