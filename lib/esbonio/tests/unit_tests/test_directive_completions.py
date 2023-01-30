import re
from functools import partial
from typing import Optional
from typing import Type

import pytest
from docutils.parsers.rst import Directive
from docutils.parsers.rst.directives.images import Image
from lsprotocol.types import ClientCapabilities
from lsprotocol.types import CompletionItem
from lsprotocol.types import CompletionItemKind
from lsprotocol.types import InsertTextFormat
from lsprotocol.types import Position
from lsprotocol.types import TextEdit
from pygls.workspace import Document
from sphinx.directives.code import CodeBlock
from sphinx.domains.c import CFunctionObject

from esbonio.lsp import CompletionContext
from esbonio.lsp.directives.completions import render_directive_completion
from esbonio.lsp.directives.completions import render_directive_option_completion
from esbonio.lsp.rst.config import ServerCompletionConfig
from esbonio.lsp.testing import range_from_str
from esbonio.lsp.util.patterns import DIRECTIVE
from esbonio.lsp.util.patterns import DIRECTIVE_OPTION


def make_completion_context(
    pattern: re.Pattern,
    text: str,
    *,
    character: int = -1,
    prefer_insert: bool = False,
) -> CompletionContext:
    """Helper for making test completion context instances.

    Parameters
    ----------
    pattern
       The regular expression pattern that corresponds to the completion request.

    text
       The text that "triggered" the completion request

    character
       The character column at which the request is being made.
       If ``-1`` (the default), it will be assumed that the request is being made at
       the end of ``text``.

    prefer_insert
       Flag to indicate if the ``preferred_insert_behavior`` option should be set to
       ``insert``
    """

    match = pattern.match(text)
    if not match:
        raise ValueError(f"'{text}' is not valid in this completion context")

    line = 0
    character = len(text) if character == -1 else character

    return CompletionContext(
        doc=Document(uri="file:///test.txt"),
        location="rst",
        match=match,
        position=Position(line=line, character=character),
        config=ServerCompletionConfig(
            preferred_insert_behavior="insert" if prefer_insert else "replace"
        ),
        capabilities=ClientCapabilities(),
    )


make_directive_completion_context = partial(make_completion_context, DIRECTIVE)
make_directive_option_completion_context = partial(
    make_completion_context, DIRECTIVE_OPTION
)


@pytest.mark.parametrize(
    "context, name, directive, expected",
    [
        (
            make_directive_completion_context(".."),
            "image",
            Image,
            CompletionItem(
                label="image",
                filter_text=".. image::",
                insert_text_format=InsertTextFormat.PlainText,
                text_edit=TextEdit(
                    range=range_from_str("0:0-0:2"), new_text=".. image::"
                ),
            ),
        ),
        (
            make_directive_completion_context(".. inc"),
            "image",
            Image,
            CompletionItem(
                label="image",
                filter_text=".. image::",
                insert_text_format=InsertTextFormat.PlainText,
                text_edit=TextEdit(
                    range=range_from_str("0:0-0:6"), new_text=".. image::"
                ),
            ),
        ),
        (
            make_directive_completion_context(".. inc", prefer_insert=True),
            "image",
            Image,
            None,
        ),
        (
            make_directive_completion_context(".. im", prefer_insert=True),
            "image",
            Image,
            CompletionItem(label="image", insert_text="image::"),
        ),
        (
            make_directive_completion_context(".. co", prefer_insert=True),
            "code-block",
            CodeBlock,
            CompletionItem(label="code-block", insert_text="code-block::"),
        ),
        (
            make_directive_completion_context(".. code-", prefer_insert=True),
            "code-block",
            CodeBlock,
            CompletionItem(label="code-block", insert_text="block::"),
        ),
        (
            make_directive_completion_context(".. code-bl", prefer_insert=True),
            "code-block",
            CodeBlock,
            CompletionItem(label="code-block", insert_text="block::"),
        ),
        (
            make_directive_completion_context("..", prefer_insert=True),
            "c:function",
            CFunctionObject,
            CompletionItem(label="c:function", insert_text=" c:function::"),
        ),
        (
            make_directive_completion_context(".. c", prefer_insert=True),
            "c:function",
            CFunctionObject,
            CompletionItem(label="c:function", insert_text="c:function::"),
        ),
        (
            make_directive_completion_context(".. c:", prefer_insert=True),
            "c:function",
            CFunctionObject,
            CompletionItem(label="c:function", insert_text="function::"),
        ),
        (
            make_directive_completion_context(".. c:fun", prefer_insert=True),
            "c:function",
            CFunctionObject,
            CompletionItem(label="c:function", insert_text="function::"),
        ),
    ],
)
def test_render_directive_completion(
    context: CompletionContext,
    name: str,
    directive: Type[Directive],
    expected: Optional[CompletionItem],
):
    """Ensure that we can render directive completions correctly, according to the
    current context."""

    # These fields are always present, so let's not force the test author to add them
    # in :)
    if expected is not None:
        expected.kind = CompletionItemKind.Class
        expected.data = {"completion_type": "directive"}

        try:
            expected.detail = f"{directive.__module__}.{directive.__name__}"
        except AttributeError:
            expected.detail = f"{directive.__module__}.{directive.__class__.__name__}"

    actual = render_directive_completion(context, name, directive)
    assert actual == expected


@pytest.mark.parametrize(
    "context, option, name, directive, expected",
    [
        (
            make_directive_option_completion_context("   :"),
            "align",
            "image",
            Image,
            CompletionItem(
                label="align",
                filter_text=":align:",
                text_edit=TextEdit(range=range_from_str("0:3-0:4"), new_text=":align:"),
            ),
        ),
        (
            make_directive_option_completion_context("   :width"),
            "align",
            "image",
            Image,
            CompletionItem(
                label="align",
                filter_text=":align:",
                text_edit=TextEdit(range=range_from_str("0:3-0:9"), new_text=":align:"),
            ),
        ),
        (
            make_directive_option_completion_context("   :width", prefer_insert=True),
            "align",
            "image",
            Image,
            None,
        ),
        (
            make_directive_option_completion_context("   :fi", prefer_insert=True),
            "figwidth",
            "image",
            Image,
            CompletionItem(label="figwidth", insert_text="figwidth:"),
        ),
        (
            make_directive_option_completion_context("   :sh", prefer_insert=True),
            "show-caption",
            "image",
            Image,
            CompletionItem(label="show-caption", insert_text="show-caption:"),
        ),
        (
            make_directive_option_completion_context("   :show-", prefer_insert=True),
            "show-caption",
            "image",
            Image,
            CompletionItem(label="show-caption", insert_text="caption:"),
        ),
        (
            make_directive_option_completion_context("   :show-c", prefer_insert=True),
            "show-caption",
            "image",
            Image,
            CompletionItem(label="show-caption", insert_text="caption:"),
        ),
    ],
)
def test_render_directive_option_completion(
    context: CompletionContext,
    option: str,
    name: str,
    directive: Type[Directive],
    expected: Optional[CompletionItem],
):
    """Ensure that we can render directive options completions correctly, according to
    the current context."""

    # These fields are always present, so let's not force the test author to add them
    # in :)
    if expected is not None:
        expected.kind = CompletionItemKind.Field
        expected.data = {"completion_type": "directive_option", "for_directive": name}

        try:
            expected.detail = f"{directive.__module__}.{directive.__name__}:{option}"
        except AttributeError:
            expected.detail = (
                f"{directive.__module__}.{directive.__class__.__name__}:{option}"
            )

    actual = render_directive_option_completion(context, option, name, directive)
    assert actual == expected
