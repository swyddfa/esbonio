"""Support for code-blocks and related directives."""
import textwrap
from typing import List

from pygls.lsp.types import CompletionItem
from pygls.lsp.types import CompletionItemKind
from pygls.lsp.types import MarkupContent
from pygls.lsp.types import MarkupKind
from pygments.lexers import get_all_lexers

from esbonio.lsp.directives import Directives
from esbonio.lsp.rst import CompletionContext
from esbonio.lsp.sphinx import SphinxLanguageServer


class CodeBlocks:
    def __init__(self, rst: SphinxLanguageServer):
        self.rst = rst
        self.logger = rst.logger.getChild(self.__class__.__name__)
        self._lexers: List[CompletionItem] = []

    @property
    def lexers(self) -> List[CompletionItem]:

        if len(self._lexers) == 0:
            self._index_lexers()

        return self._lexers

    def complete_arguments(
        self, context: CompletionContext, domain: str, name: str
    ) -> List[CompletionItem]:

        if name in {"code-block", "highlight"}:
            return self.lexers

        return []

    def _index_lexers(self):
        self._lexers = []

        for (name, labels, files, mimes) in get_all_lexers():
            for label in labels:
                documentation = f"""\
                ### {name}

                Filenames:  {', '.join(files)}

                MIME Types: {', '.join(mimes)}
                """

                item = CompletionItem(
                    label=label,
                    kind=CompletionItemKind.Constant,
                    documentation=MarkupContent(
                        kind=MarkupKind.Markdown, value=textwrap.dedent(documentation)
                    ),
                )

                self._lexers.append(item)


def esbonio_setup(rst: SphinxLanguageServer, directives: Directives):
    directives.add_argument_completion_provider(CodeBlocks(rst))
