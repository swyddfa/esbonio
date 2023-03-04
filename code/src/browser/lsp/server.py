from typing import Literal
from typing import Union

from docutils import __version__ as __docutils_version__
from lsprotocol.types import InitializedParams
from pygls.protocol import default_converter

from esbonio.lsp import __version__
from esbonio.lsp import create_language_server
from esbonio.lsp.rst import DEFAULT_MODULES
from esbonio.lsp.rst import LanguageFeature
from esbonio.lsp.rst import RstLanguageServer


class DocutilsVersion(LanguageFeature):
    """Quick hack to get the version number into the client."""

    def initialized(self, params: InitializedParams) -> None:
        self.rst.send_notification(
            "esbonio/buildComplete", {"docutils": {"version": __docutils_version__}}
        )


def esbonio_converter():
    converter = default_converter()
    converter.register_structure_hook(Union[Literal["auto"], int], lambda obj, _: obj)

    return converter


# For now, let's just try the basic rst language server.
# Eventually... it should be possible to create one of these per entry
# point and have the web extension switch between them.
server = create_language_server(
    RstLanguageServer,
    DEFAULT_MODULES,
    name="esbonio",
    version=__version__,
    converter_factory=esbonio_converter,
)
server.add_feature(DocutilsVersion(server))
server.start_pyodide()
