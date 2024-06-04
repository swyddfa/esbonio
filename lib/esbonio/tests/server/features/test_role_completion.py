from __future__ import annotations

import typing

import pytest
from lsprotocol import types
from pygls.workspace import TextDocument
from pytest_lsp import client_capabilities

from esbonio import server
from esbonio.server.features.roles import completion
from esbonio.server.testing import range_from_str
from esbonio.sphinx_agent.types import RST_ROLE
from esbonio.sphinx_agent.types import Role

if typing.TYPE_CHECKING:
    from typing import Literal
    from typing import Optional


VSCODE = "visual-studio-code"
NVIM = "neovim"
PATTERNS = {"rst": RST_ROLE}


@pytest.mark.parametrize(
    "client,language,insert_behavior,role,text,character,expected",
    [
        (
            VSCODE,
            "rst",
            "replace",
            Role("ref", "sphinx.roles.XRefRole"),
            ":",
            None,
            types.CompletionItem(
                label="ref",
                detail="sphinx.roles.XRefRole",
                kind=types.CompletionItemKind.Function,
                filter_text=":ref:",
                insert_text_format=types.InsertTextFormat.PlainText,
                text_edit=types.TextEdit(
                    range=range_from_str("0:0-0:1"), new_text=":ref:"
                ),
                data={"completion_type": "role"},
            ),
        ),
        (
            VSCODE,
            "rst",
            "replace",
            Role("ref", "sphinx.roles.XRefRole"),
            ":r",
            None,
            types.CompletionItem(
                label="ref",
                detail="sphinx.roles.XRefRole",
                kind=types.CompletionItemKind.Function,
                filter_text=":ref:",
                insert_text_format=types.InsertTextFormat.PlainText,
                text_edit=types.TextEdit(
                    range=range_from_str("0:0-0:2"), new_text=":ref:"
                ),
                data={"completion_type": "role"},
            ),
        ),
        (
            VSCODE,
            "rst",
            "replace",
            Role("ref", "sphinx.roles.XRefRole"),
            ":doc",
            None,
            types.CompletionItem(
                label="ref",
                detail="sphinx.roles.XRefRole",
                kind=types.CompletionItemKind.Function,
                filter_text=":ref:",
                insert_text_format=types.InsertTextFormat.PlainText,
                text_edit=types.TextEdit(
                    range=range_from_str("0:0-0:4"), new_text=":ref:"
                ),
                data={"completion_type": "role"},
            ),
        ),
        (
            VSCODE,
            "rst",
            "replace",
            Role("cpp:func", "sphinx.domains.cpp.CPPXRefRole"),
            ":c",
            None,
            types.CompletionItem(
                label="cpp:func",
                detail="sphinx.domains.cpp.CPPXRefRole",
                kind=types.CompletionItemKind.Function,
                filter_text=":cpp:func:",
                insert_text_format=types.InsertTextFormat.PlainText,
                text_edit=types.TextEdit(
                    range=range_from_str("0:0-0:2"), new_text=":cpp:func:"
                ),
                data={"completion_type": "role"},
            ),
        ),
        (
            VSCODE,
            "rst",
            "replace",
            Role("cpp:func", "sphinx.domains.cpp.CPPXRefRole"),
            ":cpp:f",
            None,
            types.CompletionItem(
                label="cpp:func",
                detail="sphinx.domains.cpp.CPPXRefRole",
                kind=types.CompletionItemKind.Function,
                filter_text=":cpp:func:",
                insert_text_format=types.InsertTextFormat.PlainText,
                text_edit=types.TextEdit(
                    range=range_from_str("0:0-0:6"), new_text=":cpp:func:"
                ),
                data={"completion_type": "role"},
            ),
        ),
        (
            VSCODE,
            "rst",
            "insert",
            Role("ref", "sphinx.roles.XRefRole"),
            ":",
            None,
            types.CompletionItem(
                label="ref",
                detail="sphinx.roles.XRefRole",
                kind=types.CompletionItemKind.Function,
                insert_text="ref:",
                insert_text_format=types.InsertTextFormat.PlainText,
                data={"completion_type": "role"},
            ),
        ),
        (
            VSCODE,
            "rst",
            "insert",
            Role("ref", "sphinx.roles.XRefRole"),
            ":r",
            None,
            types.CompletionItem(
                label="ref",
                detail="sphinx.roles.XRefRole",
                kind=types.CompletionItemKind.Function,
                insert_text="ref:",
                insert_text_format=types.InsertTextFormat.PlainText,
                data={"completion_type": "role"},
            ),
        ),
        (
            VSCODE,
            "rst",
            "insert",
            Role("ref", "sphinx.roles.XRefRole"),
            ":doc",
            None,
            None,
        ),
        (
            VSCODE,
            "rst",
            "insert",
            Role("cpp:func", "sphinx.domains.cpp.CPPXRefRole"),
            ":c",
            None,
            types.CompletionItem(
                label="cpp:func",
                detail="sphinx.domains.cpp.CPPXRefRole",
                kind=types.CompletionItemKind.Function,
                insert_text="cpp:func:",
                insert_text_format=types.InsertTextFormat.PlainText,
                data={"completion_type": "role"},
            ),
        ),
        (
            VSCODE,
            "rst",
            "insert",
            Role("cpp:func", "sphinx.domains.cpp.CPPXRefRole"),
            ":cpp:",
            None,
            types.CompletionItem(
                label="cpp:func",
                detail="sphinx.domains.cpp.CPPXRefRole",
                kind=types.CompletionItemKind.Function,
                insert_text="func:",
                insert_text_format=types.InsertTextFormat.PlainText,
                data={"completion_type": "role"},
            ),
        ),
        (
            VSCODE,
            "rst",
            "insert",
            Role("cpp:func", "sphinx.domains.cpp.CPPXRefRole"),
            ":cpp:f",
            None,
            types.CompletionItem(
                label="cpp:func",
                detail="sphinx.domains.cpp.CPPXRefRole",
                kind=types.CompletionItemKind.Function,
                insert_text="func:",
                insert_text_format=types.InsertTextFormat.PlainText,
                data={"completion_type": "role"},
            ),
        ),
    ],
)
def test_render_role_completion(
    client: str,
    language: Literal["rst", "markdown"],
    insert_behavior: Literal["insert", "replace"],
    role: Role,
    text: str,
    character: Optional[int],
    expected: Optional[types.CompletionItem],
):
    """Ensure that we can render role completions correctly.

    Parameters
    ----------
    client
       The name of the client to use.

       This will be passed to the ``client_capabilities`` function from ``pytest_lsp``
       and controls which capabilities (e.g. snippet support) will be available.

    language
       The language in which the completion item will be inserted.

    insert_behavior
       How the completion item should behave when inserted

    role
       The role to generate the completion item for

    text
       The text used to help generate the completion context.

    character
       The character column at which the request is being made.
       If ``None``, it will be assumed that the request is being made at the end of ``text``

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

    render_func = completion.get_role_renderer(language, insert_behavior)
    assert render_func is not None

    item = render_func(context, role)
    if expected is None:
        assert item is None
    else:
        assert item == expected
