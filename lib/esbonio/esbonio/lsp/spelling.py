"""Spell checking."""
import re
from typing import Dict
from typing import List
from typing import Optional

import pygls.uris as Uri
from docutils import nodes
from pygls.lsp.types import CodeAction
from pygls.lsp.types import CodeActionKind
from pygls.lsp.types import CodeActionParams
from pygls.lsp.types import TextEdit
from pygls.lsp.types import WorkspaceEdit
from pygls.lsp.types.basic_structures import Diagnostic
from pygls.lsp.types.basic_structures import DiagnosticSeverity
from pygls.lsp.types.basic_structures import Position
from pygls.lsp.types.basic_structures import Range
from pygls.lsp.types.workspace import DidSaveTextDocumentParams
from spellchecker import SpellChecker  # type: ignore

from esbonio.lsp.rst import LanguageFeature
from esbonio.lsp.sphinx import SphinxLanguageServer

IGNORED_NODES = {nodes.raw, nodes.literal, nodes.literal_block}
"""Don't spell check Text contained in any of these nodes."""


class Spelling(LanguageFeature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.lang = SpellChecker()
        self.errors: Dict[str, List[MisSpelling]] = {}

    def code_action(self, params: CodeActionParams) -> List[CodeAction]:
        uri = params.text_document.uri
        ranges = {d.range for d in params.context.diagnostics}

        if uri in self.errors:
            errors = self.errors[uri]
        else:
            errors = self.find_errors_for_uri(uri)

        diagnostics = errors_to_diagnostics(errors)
        actions = []

        for error, diagnostic in zip(errors, diagnostics):
            if len(ranges) > 0 and diagnostic.range not in ranges:
                continue

            for fix in self.lang.candidates(error.text):
                actions.append(
                    CodeAction(
                        title=f"Correct '{error.text}' -> '{fix}'",
                        kind=CodeActionKind.QuickFix,
                        diagnostics=[diagnostic],
                        edit=WorkspaceEdit(
                            changes={
                                uri: [TextEdit(range=diagnostic.range, new_text=fix)]
                            }
                        ),
                    )
                )

        return actions

    def save(self, params: DidSaveTextDocumentParams):
        self.find_errors_for_uri(params.text_document.uri)

    def find_errors_for_uri(self, uri: str) -> List["MisSpelling"]:
        """Find any mis-spellings in the given document."""

        doctree = self.rst.get_doctree(uri=uri)
        if doctree is None:
            return []

        errors = []

        for text in doctree.traverse(condition=nodes.Text):
            parent = text.parent
            # Don't spell check code block, raw blocks etc.

            if type(parent) in IGNORED_NODES:
                continue

            # Don't spell check text we cannot tie back to the user's actual source file
            self.logger.debug("%s: %s", type(parent), parent.source)
            if parent.source != Uri.to_fs_path(uri):
                continue

            for word in find_words(
                text.astext(), startline=parent.line, source=parent.source
            ):
                # Ignore short words or any "word" that contains digits or other
                # punctuation.
                if len(word) <= 1 or re.search("[-/\\_\\d.=']", str(word)):
                    continue

                if self.lang.unknown([str(word)]):
                    errors.append(word)

        self.errors[uri] = errors
        self.rst.set_diagnostics("spellcheck[en]", uri, errors_to_diagnostics(errors))
        self.rst.sync_diagnostics()

        return errors


class MisSpelling:
    """Represents an incorrectly spelled word."""

    def __init__(self, line: int, character: int, text: str, source: Optional[str]):
        self.line = line
        self.character = character
        self.text = text
        self.source = source

    def __str__(self):
        return self.text

    def __contains__(self, item):
        return item in self.text

    def __len__(self):
        return len(self.text)

    def __repr__(self):
        return f"MisSpelling<{self.line}:{self.character}, {self.text}>"


def errors_to_diagnostics(errors: List[MisSpelling]) -> List[Diagnostic]:
    diagnostics = []

    for error in errors:
        range_ = Range(
            start=Position(line=error.line - 1, character=error.character),
            end=Position(line=error.line - 1, character=error.character + len(error)),
        )

        diagnostics.append(
            Diagnostic(
                range=range_,
                message=f"Incorrect spelling: '{error}'",
                severity=DiagnosticSeverity.Warning,
                source="spellcheck[en]",
            )
        )

    return diagnostics


def find_words(
    text: str, startline: int = 0, source: Optional[str] = None
) -> List[MisSpelling]:
    words = []
    delimiters = " \n"
    skip_characters = ",'\"()[]"
    current_word = None

    line = startline
    col = -1

    for c in text:
        col += 1

        if c in skip_characters:
            continue

        if c not in delimiters:
            if current_word is None:
                current_word = MisSpelling(line, col, c, source)
            else:
                current_word.text += c
        else:
            if current_word is not None:
                words.append(current_word)
                current_word = None

            if c == "\n":
                line += 1
                col = -1

    if current_word is not None:
        words.append(current_word)

    return words


def esbonio_setup(rst: SphinxLanguageServer):
    rst.add_feature(Spelling(rst))
