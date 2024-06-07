from __future__ import annotations

import typing

import pytest
from lsprotocol import types
from pygls.workspace import TextDocument
from pytest_lsp import client_capabilities

from esbonio import server
from esbonio.server.features.directives import Directive
from esbonio.server.features.directives import completion
from esbonio.server.testing import range_from_str
from esbonio.sphinx_agent.types import MYST_DIRECTIVE
from esbonio.sphinx_agent.types import RST_DIRECTIVE

if typing.TYPE_CHECKING:
    from typing import Literal
    from typing import Optional


VSCODE = "visual-studio-code"
NVIM = "neovim"
PATTERNS = {"rst": RST_DIRECTIVE, "markdown": MYST_DIRECTIVE}


@pytest.mark.parametrize(
    "client,language,insert_behavior,directive,text,character,expected",
    [
        (  # Standard rst directive completion with replacement
            VSCODE,
            "rst",
            "replace",
            Directive(
                name="image",
                implementation="docutils.parsers.rst.directives.images.Image",
            ),
            "..",
            None,
            types.CompletionItem(
                label="image",
                detail="docutils.parsers.rst.directives.images.Image",
                kind=types.CompletionItemKind.Class,
                filter_text=".. image::",
                insert_text_format=types.InsertTextFormat.PlainText,
                text_edit=types.TextEdit(
                    range=range_from_str("0:0-0:2"), new_text=".. image::"
                ),
                data=dict(completion_type="directive"),
            ),
        ),
        (  # We need to take into account indentation
            VSCODE,
            "rst",
            "replace",
            Directive(
                name="image",
                implementation="docutils.parsers.rst.directives.images.Image",
            ),
            "   ..",
            None,
            types.CompletionItem(
                label="image",
                detail="docutils.parsers.rst.directives.images.Image",
                kind=types.CompletionItemKind.Class,
                filter_text=".. image::",
                insert_text_format=types.InsertTextFormat.PlainText,
                text_edit=types.TextEdit(
                    range=range_from_str("0:3-0:5"), new_text=".. image::"
                ),
                data=dict(completion_type="directive"),
            ),
        ),
        (  # The replacement should remove all exiting text
            VSCODE,
            "rst",
            "replace",
            Directive(
                name="image",
                implementation="docutils.parsers.rst.directives.images.Image",
            ),
            ".. inc",
            None,
            types.CompletionItem(
                label="image",
                detail="docutils.parsers.rst.directives.images.Image",
                kind=types.CompletionItemKind.Class,
                filter_text=".. image::",
                insert_text_format=types.InsertTextFormat.PlainText,
                text_edit=types.TextEdit(
                    range=range_from_str("0:0-0:6"), new_text=".. image::"
                ),
                data=dict(completion_type="directive"),
            ),
        ),
        (  # Unless the directive has an existing argument, then we should not replace
            # it
            VSCODE,
            "rst",
            "replace",
            Directive(
                name="image",
                implementation="docutils.parsers.rst.directives.images.Image",
            ),
            ".. include:: filename.png",
            3,  # character
            types.CompletionItem(
                label="image",
                detail="docutils.parsers.rst.directives.images.Image",
                kind=types.CompletionItemKind.Class,
                filter_text=".. image::",
                insert_text_format=types.InsertTextFormat.PlainText,
                text_edit=types.TextEdit(
                    range=range_from_str("0:0-0:12"), new_text=".. image::"
                ),
                data=dict(completion_type="directive"),
            ),
        ),
        (  # When doing 'insert' completions, we should skip directives with
            # incompatible prefixes
            VSCODE,
            "rst",
            "insert",
            Directive(
                name="image",
                implementation="docutils.parsers.rst.directives.images.Image",
            ),
            ".. inc",
            None,
            None,
        ),
        (  # 'insert' completions still do some replacement, but it's up to the client's
            # interpretation of what is considered a 'word'
            VSCODE,
            "rst",
            "insert",
            Directive(
                name="image",
                implementation="docutils.parsers.rst.directives.images.Image",
            ),
            ".. im",
            None,
            types.CompletionItem(
                label="image",
                detail="docutils.parsers.rst.directives.images.Image",
                kind=types.CompletionItemKind.Class,
                insert_text="image::",
                insert_text_format=types.InsertTextFormat.PlainText,
                data=dict(completion_type="directive"),
            ),
        ),
        (
            VSCODE,
            "rst",
            "insert",
            Directive(
                name="code-block",
                implementation="sphinx.directives.code.CodeBlock",
            ),
            ".. co",
            None,
            types.CompletionItem(
                label="code-block",
                detail="sphinx.directives.code.CodeBlock",
                kind=types.CompletionItemKind.Class,
                insert_text="code-block::",
                insert_text_format=types.InsertTextFormat.PlainText,
                data=dict(completion_type="directive"),
            ),
        ),
        (
            VSCODE,
            "rst",
            "insert",
            Directive(
                name="code-block",
                implementation="sphinx.directives.code.CodeBlock",
            ),
            ".. code-",
            None,
            types.CompletionItem(
                label="code-block",
                detail="sphinx.directives.code.CodeBlock",
                kind=types.CompletionItemKind.Class,
                insert_text="block::",
                insert_text_format=types.InsertTextFormat.PlainText,
                data=dict(completion_type="directive"),
            ),
        ),
        (
            VSCODE,
            "rst",
            "insert",
            Directive(
                name="code-block",
                implementation="sphinx.directives.code.CodeBlock",
            ),
            ".. code-bl",
            None,
            types.CompletionItem(
                label="code-block",
                detail="sphinx.directives.code.CodeBlock",
                kind=types.CompletionItemKind.Class,
                insert_text="block::",
                insert_text_format=types.InsertTextFormat.PlainText,
                data=dict(completion_type="directive"),
            ),
        ),
        (
            VSCODE,
            "rst",
            "insert",
            Directive(
                name="c:function",
                implementation="sphinx.domains.c.CFunctionObject",
            ),
            "..",
            None,
            types.CompletionItem(
                label="c:function",
                detail="sphinx.domains.c.CFunctionObject",
                kind=types.CompletionItemKind.Class,
                insert_text=" c:function::",
                insert_text_format=types.InsertTextFormat.PlainText,
                data=dict(completion_type="directive"),
            ),
        ),
        (
            VSCODE,
            "rst",
            "insert",
            Directive(
                name="c:function",
                implementation="sphinx.domains.c.CFunctionObject",
            ),
            ".. c",
            None,
            types.CompletionItem(
                label="c:function",
                detail="sphinx.domains.c.CFunctionObject",
                kind=types.CompletionItemKind.Class,
                insert_text="c:function::",
                insert_text_format=types.InsertTextFormat.PlainText,
                data=dict(completion_type="directive"),
            ),
        ),
        (
            VSCODE,
            "rst",
            "insert",
            Directive(
                name="c:function",
                implementation="sphinx.domains.c.CFunctionObject",
            ),
            ".. c:",
            None,
            types.CompletionItem(
                label="c:function",
                detail="sphinx.domains.c.CFunctionObject",
                kind=types.CompletionItemKind.Class,
                insert_text="function::",
                insert_text_format=types.InsertTextFormat.PlainText,
                data=dict(completion_type="directive"),
            ),
        ),
        (
            VSCODE,
            "rst",
            "insert",
            Directive(
                name="c:function",
                implementation="sphinx.domains.c.CFunctionObject",
            ),
            ".. c:fun",
            None,
            types.CompletionItem(
                label="c:function",
                detail="sphinx.domains.c.CFunctionObject",
                kind=types.CompletionItemKind.Class,
                insert_text="function::",
                insert_text_format=types.InsertTextFormat.PlainText,
                data=dict(completion_type="directive"),
            ),
        ),
        (  # If the client supports it, we can use snippets to include the closing fences
            VSCODE,
            "markdown",
            "replace",
            Directive(
                name="image",
                implementation="docutils.parsers.rst.directives.images.Image",
            ),
            """```""",
            None,
            types.CompletionItem(
                label="image",
                detail="docutils.parsers.rst.directives.images.Image",
                kind=types.CompletionItemKind.Class,
                filter_text="```{image} $0\n```",
                insert_text_format=types.InsertTextFormat.Snippet,
                text_edit=types.TextEdit(
                    range=range_from_str("0:0-0:3"), new_text="```{image} $0\n```"
                ),
                data=dict(completion_type="directive"),
            ),
        ),
        (  # Otherwise, they should be omitted
            NVIM,
            "markdown",
            "replace",
            Directive(
                name="image",
                implementation="docutils.parsers.rst.directives.images.Image",
            ),
            """```""",
            None,
            types.CompletionItem(
                label="image",
                detail="docutils.parsers.rst.directives.images.Image",
                kind=types.CompletionItemKind.Class,
                filter_text="```{image}",
                insert_text_format=types.InsertTextFormat.PlainText,
                text_edit=types.TextEdit(
                    range=range_from_str("0:0-0:3"), new_text="```{image}"
                ),
                data=dict(completion_type="directive"),
            ),
        ),
        (  # Be sure to take into account indentation
            VSCODE,
            "markdown",
            "replace",
            Directive(
                name="image",
                implementation="docutils.parsers.rst.directives.images.Image",
            ),
            """   ```""",
            None,
            types.CompletionItem(
                label="image",
                detail="docutils.parsers.rst.directives.images.Image",
                kind=types.CompletionItemKind.Class,
                filter_text="```{image} $0\n```",
                insert_text_format=types.InsertTextFormat.Snippet,
                text_edit=types.TextEdit(
                    range=range_from_str("0:3-0:6"), new_text="```{image} $0\n```"
                ),
                data=dict(completion_type="directive"),
            ),
        ),
        (
            VSCODE,
            "markdown",
            "replace",
            Directive(
                name="image",
                implementation="docutils.parsers.rst.directives.images.Image",
            ),
            """```{inc""",
            None,
            types.CompletionItem(
                label="image",
                detail="docutils.parsers.rst.directives.images.Image",
                kind=types.CompletionItemKind.Class,
                filter_text="```{image} $0\n```",
                insert_text_format=types.InsertTextFormat.Snippet,
                text_edit=types.TextEdit(
                    range=range_from_str("0:0-0:7"), new_text="```{image} $0\n```"
                ),
                data=dict(completion_type="directive"),
            ),
        ),
        (
            NVIM,
            "markdown",
            "replace",
            Directive(
                name="image",
                implementation="docutils.parsers.rst.directives.images.Image",
            ),
            """```{inc""",
            None,
            types.CompletionItem(
                label="image",
                detail="docutils.parsers.rst.directives.images.Image",
                kind=types.CompletionItemKind.Class,
                filter_text="```{image}",
                insert_text_format=types.InsertTextFormat.PlainText,
                text_edit=types.TextEdit(
                    range=range_from_str("0:0-0:7"), new_text="```{image}"
                ),
                data=dict(completion_type="directive"),
            ),
        ),
        (  # Arguments should not be replaced
            VSCODE,
            "markdown",
            "replace",
            Directive(
                name="image",
                implementation="docutils.parsers.rst.directives.images.Image",
            ),
            """```{include} filename.png""",
            7,  # character index
            types.CompletionItem(
                label="image",
                detail="docutils.parsers.rst.directives.images.Image",
                kind=types.CompletionItemKind.Class,
                filter_text="```{image}",
                insert_text_format=types.InsertTextFormat.PlainText,
                text_edit=types.TextEdit(
                    range=range_from_str("0:0-0:12"), new_text="```{image}"
                ),
                data=dict(completion_type="directive"),
            ),
        ),
        (
            VSCODE,
            "markdown",
            "insert",
            Directive(
                name="image",
                implementation="docutils.parsers.rst.directives.images.Image",
            ),
            """```{inc""",
            None,
            None,
        ),
        (
            VSCODE,
            "markdown",
            "insert",
            Directive(
                name="image",
                implementation="docutils.parsers.rst.directives.images.Image",
            ),
            "```",
            None,
            types.CompletionItem(
                label="image",
                detail="docutils.parsers.rst.directives.images.Image",
                kind=types.CompletionItemKind.Class,
                insert_text="{image} $0\n```",
                insert_text_format=types.InsertTextFormat.Snippet,
                data=dict(completion_type="directive"),
            ),
        ),
        (
            VSCODE,
            "markdown",
            "insert",
            Directive(
                name="image",
                implementation="docutils.parsers.rst.directives.images.Image",
            ),
            "```{",
            None,
            types.CompletionItem(
                label="image",
                detail="docutils.parsers.rst.directives.images.Image",
                kind=types.CompletionItemKind.Class,
                insert_text="image} $0\n```",
                insert_text_format=types.InsertTextFormat.Snippet,
                data=dict(completion_type="directive"),
            ),
        ),
        (
            VSCODE,
            "markdown",
            "insert",
            Directive(
                name="image",
                implementation="docutils.parsers.rst.directives.images.Image",
            ),
            "```{im",
            None,
            types.CompletionItem(
                label="image",
                detail="docutils.parsers.rst.directives.images.Image",
                kind=types.CompletionItemKind.Class,
                insert_text="image} $0\n```",
                insert_text_format=types.InsertTextFormat.Snippet,
                data=dict(completion_type="directive"),
            ),
        ),
        (
            NVIM,
            "markdown",
            "insert",
            Directive(
                name="image",
                implementation="docutils.parsers.rst.directives.images.Image",
            ),
            "```{im",
            None,
            types.CompletionItem(
                label="image",
                detail="docutils.parsers.rst.directives.images.Image",
                kind=types.CompletionItemKind.Class,
                insert_text="image}",
                insert_text_format=types.InsertTextFormat.PlainText,
                data=dict(completion_type="directive"),
            ),
        ),
        (
            NVIM,
            "markdown",
            "insert",
            Directive(
                name="code-block",
                implementation="sphinx.directives.code.CodeBlock",
            ),
            "```{co",
            None,
            types.CompletionItem(
                label="code-block",
                detail="sphinx.directives.code.CodeBlock",
                kind=types.CompletionItemKind.Class,
                insert_text="code-block}",
                insert_text_format=types.InsertTextFormat.PlainText,
                data=dict(completion_type="directive"),
            ),
        ),
        (
            NVIM,
            "markdown",
            "insert",
            Directive(
                name="code-block",
                implementation="sphinx.directives.code.CodeBlock",
            ),
            "```{code-",
            None,
            types.CompletionItem(
                label="code-block",
                detail="sphinx.directives.code.CodeBlock",
                kind=types.CompletionItemKind.Class,
                insert_text="block}",
                insert_text_format=types.InsertTextFormat.PlainText,
                data=dict(completion_type="directive"),
            ),
        ),
        (
            NVIM,
            "markdown",
            "insert",
            Directive(
                name="code-block",
                implementation="sphinx.directives.code.CodeBlock",
            ),
            "```{code-bl",
            None,
            types.CompletionItem(
                label="code-block",
                detail="sphinx.directives.code.CodeBlock",
                kind=types.CompletionItemKind.Class,
                insert_text="block}",
                insert_text_format=types.InsertTextFormat.PlainText,
                data=dict(completion_type="directive"),
            ),
        ),
        (
            NVIM,
            "markdown",
            "insert",
            Directive(
                name="c:function",
                implementation="sphinx.domains.c.CFunctionObject",
            ),
            "```",
            None,
            types.CompletionItem(
                label="c:function",
                detail="sphinx.domains.c.CFunctionObject",
                kind=types.CompletionItemKind.Class,
                insert_text="{c:function}",
                insert_text_format=types.InsertTextFormat.PlainText,
                data=dict(completion_type="directive"),
            ),
        ),
        (
            NVIM,
            "markdown",
            "insert",
            Directive(
                name="c:function",
                implementation="sphinx.domains.c.CFunctionObject",
            ),
            "```{c",
            None,
            types.CompletionItem(
                label="c:function",
                detail="sphinx.domains.c.CFunctionObject",
                kind=types.CompletionItemKind.Class,
                insert_text="c:function}",
                insert_text_format=types.InsertTextFormat.PlainText,
                data=dict(completion_type="directive"),
            ),
        ),
        (
            NVIM,
            "markdown",
            "insert",
            Directive(
                name="c:function",
                implementation="sphinx.domains.c.CFunctionObject",
            ),
            "```{c:",
            None,
            types.CompletionItem(
                label="c:function",
                detail="sphinx.domains.c.CFunctionObject",
                kind=types.CompletionItemKind.Class,
                insert_text="function}",
                insert_text_format=types.InsertTextFormat.PlainText,
                data=dict(completion_type="directive"),
            ),
        ),
        (
            NVIM,
            "markdown",
            "insert",
            Directive(
                name="c:function",
                implementation="sphinx.domains.c.CFunctionObject",
            ),
            "```{c:fun",
            None,
            types.CompletionItem(
                label="c:function",
                detail="sphinx.domains.c.CFunctionObject",
                kind=types.CompletionItemKind.Class,
                insert_text="function}",
                insert_text_format=types.InsertTextFormat.PlainText,
                data=dict(completion_type="directive"),
            ),
        ),
    ],
)
def test_render_directive_completion(
    client: str,
    language: Literal["rst", "markdown"],
    insert_behavior: Literal["insert", "replace"],
    directive: Directive,
    text: str,
    character: Optional[int],
    expected: Optional[types.CompletionItem],
):
    """Ensure that we can render directive completions correctly.

    Parameters
    ----------
    client
       The name of the client to use.

       This will be passed to the ``client_capabilities`` function from ``pytest_lsp``
       and will control what capabilities (e.g. snippet support) will be available.

    language
       The language in which the completion item will be inserted.

    insert_behavior
       How the completion item should behave when inserted.

    directive
       The directive to generate the completion item for.

    text
       The text used to help generate the completion context.

    character
       The character column at which the request is being made.
       If ``None``, it will be assumed that the request is being made at
       the end of ``text``.

    expected
       The expected result.
    """

    match = PATTERNS[language].match(text)
    if not match:
        raise ValueError(f"'{text}' is not valid in this context")

    line = 0
    character = len(text) if character is None else character
    uri = "file:///test.txt"

    context = server.CompletionContext(
        uri=server.Uri.parse(uri),
        doc=TextDocument(uri=uri),
        match=match,
        position=types.Position(line=line, character=character),
        language=language,
        capabilities=client_capabilities(client),
    )

    render_func = completion.get_directive_renderer(language, insert_behavior)
    assert render_func is not None

    item = render_func(context, directive)
    if expected is None:
        assert item is None
    else:
        assert item == expected
