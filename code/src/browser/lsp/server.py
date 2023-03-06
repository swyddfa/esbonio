from typing import Literal
from typing import Union

from pygls.protocol import default_converter

from esbonio.lsp import __version__
from esbonio.lsp import create_language_server
from esbonio.lsp.sphinx import DEFAULT_MODULES
from esbonio.lsp.sphinx import SphinxLanguageServer


def esbonio_converter():
    converter = default_converter()
    converter.register_structure_hook(Union[Literal["auto"], int], lambda obj, _: obj)

    return converter


server = create_language_server(
    SphinxLanguageServer,
    DEFAULT_MODULES,
    name="esbonio",
    version=__version__,
    converter_factory=esbonio_converter,
)
server.start_pyodide()
