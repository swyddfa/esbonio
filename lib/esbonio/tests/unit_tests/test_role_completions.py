from functools import partial
from typing import Any
from typing import Optional

import pytest
from lsprotocol.types import CompletionItem
from lsprotocol.types import CompletionItemKind
from lsprotocol.types import TextEdit
from sphinx.domains.cpp import CPPXRefRole
from sphinx.roles import XRefRole

from esbonio.lsp import CompletionContext
from esbonio.lsp.roles.completions import render_role_completion
from esbonio.lsp.testing import make_completion_context
from esbonio.lsp.testing import range_from_str
from esbonio.lsp.util.patterns import ROLE

make_role_completion_context = partial(make_completion_context, ROLE)


@pytest.mark.parametrize(
    "context, name, role, expected",
    [
        (
            make_role_completion_context(":"),
            "ref",
            XRefRole,
            CompletionItem(
                label="ref",
                filter_text=":ref:",
                text_edit=TextEdit(range=range_from_str("0:0-0:1"), new_text=":ref:"),
            ),
        ),
        (
            make_role_completion_context(":r"),
            "ref",
            XRefRole,
            CompletionItem(
                label="ref",
                filter_text=":ref:",
                text_edit=TextEdit(range=range_from_str("0:0-0:2"), new_text=":ref:"),
            ),
        ),
        (
            make_role_completion_context(":doc"),
            "ref",
            XRefRole,
            CompletionItem(
                label="ref",
                filter_text=":ref:",
                text_edit=TextEdit(range=range_from_str("0:0-0:4"), new_text=":ref:"),
            ),
        ),
        (
            make_role_completion_context(":c"),
            "cpp:func",
            CPPXRefRole,
            CompletionItem(
                label="cpp:func",
                filter_text=":cpp:func:",
                text_edit=TextEdit(
                    range=range_from_str("0:0-0:2"), new_text=":cpp:func:"
                ),
            ),
        ),
        (
            make_role_completion_context(":cpp:f"),
            "cpp:func",
            CPPXRefRole,
            CompletionItem(
                label="cpp:func",
                filter_text=":cpp:func:",
                text_edit=TextEdit(
                    range=range_from_str("0:0-0:6"), new_text=":cpp:func:"
                ),
            ),
        ),
        (
            make_role_completion_context(":", prefer_insert=True),
            "ref",
            XRefRole,
            CompletionItem(label="ref", insert_text="ref:"),
        ),
        (
            make_role_completion_context(":r", prefer_insert=True),
            "ref",
            XRefRole,
            CompletionItem(label="ref", insert_text="ref:"),
        ),
        (
            make_role_completion_context(":doc", prefer_insert=True),
            "ref",
            XRefRole,
            None,
        ),
        (
            make_role_completion_context(":c", prefer_insert=True),
            "cpp:func",
            CPPXRefRole,
            CompletionItem(label="cpp:func", insert_text="cpp:func:"),
        ),
        (
            make_role_completion_context(":cpp:", prefer_insert=True),
            "cpp:func",
            CPPXRefRole,
            CompletionItem(label="cpp:func", insert_text="func:"),
        ),
        (
            make_role_completion_context(":cpp:f", prefer_insert=True),
            "cpp:func",
            CPPXRefRole,
            CompletionItem(label="cpp:func", insert_text="func:"),
        ),
    ],
)
def test_render_role_completion(
    context: CompletionContext, name: str, role: Any, expected: Optional[CompletionItem]
):
    """Ensure that we can render role completions correctly, according to the current
    context."""

    # These fields are always present, so let's not force the test author to add them
    # each time :)

    if expected is not None:
        expected.kind = CompletionItemKind.Function
        expected.data = {"completion_type": "role"}

        try:
            expected.detail = f"{role.__module__}.{role.__name__}"
        except AttributeError:
            expected.detail = f"{role.__module__}.{role.__class__.__name__}"

    actual = render_role_completion(context, name, role)
    assert actual == expected
