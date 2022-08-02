from docutils import __version__
from pygls.lsp.types import InitializedParams

from esbonio.lsp import create_language_server
from esbonio.lsp.rst import DEFAULT_MODULES
from esbonio.lsp.rst import LanguageFeature
from esbonio.lsp.rst import RstLanguageServer


class DocutilsVersion(LanguageFeature):
    """Quick hack to get the version number into the client."""

    def initialized(self, params: InitializedParams) -> None:
        self.rst.send_notification(
            "esbonio/buildComplete", {"docutils": {"version": __version__}}
        )


# For now, let's just try the basic rst language server.
# Eventually... it should be possible to create one of these per entry
# point and have the web extension switch between them.
server = create_language_server(RstLanguageServer, DEFAULT_MODULES)
server.add_feature(DocutilsVersion(server))
server.start_pyodide()
