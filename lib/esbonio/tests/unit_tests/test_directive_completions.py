from functools import partial
from typing import Optional
from typing import Type

import pytest
from docutils.parsers.rst import Directive
from docutils.parsers.rst.directives.images import Image
from lsprotocol.types import CompletionItem
from lsprotocol.types import CompletionItemKind
from lsprotocol.types import TextEdit

from esbonio.lsp import CompletionContext
from esbonio.lsp.directives.completions import render_directive_option_completion
from esbonio.lsp.testing import make_completion_context
from esbonio.lsp.testing import range_from_str
from esbonio.lsp.util.patterns import DIRECTIVE_OPTION

make_directive_option_completion_context = partial(
    make_completion_context, DIRECTIVE_OPTION
)


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
