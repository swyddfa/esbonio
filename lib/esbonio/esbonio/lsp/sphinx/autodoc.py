from typing import Iterable
from typing import Optional

from esbonio.lsp import CompletionContext
from esbonio.lsp.directives import DirectiveLanguageFeature
from esbonio.lsp.directives import Directives
from esbonio.lsp.sphinx import SphinxLanguageServer


class AutoDoc(DirectiveLanguageFeature):
    def __init__(self, rst: SphinxLanguageServer):
        self.rst = rst

    def suggest_options(
        self, context: CompletionContext, directive: str, domain: Optional[str]
    ) -> Iterable[str]:

        if self.rst.app is None or not directive.startswith("auto"):
            return []

        # The autoxxxx set of directives need special support as their options are
        # stored on "documenters" instead of the directive implementation itself.
        name = directive.replace("auto", "")
        documenter = self.rst.app.registry.documenters.get(name, None)

        if documenter is None:
            self.rst.logger.debug(
                "Unable to find documenter for directive: '%s'", directive
            )
            return []

        return documenter.option_spec.keys()


def esbonio_setup(rst: SphinxLanguageServer, directives: Directives):
    directives.add_feature(AutoDoc(rst))
