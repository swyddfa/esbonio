from typing import Optional
from typing import Set

import pytest
from pygls.lsp.types import MarkupKind
from pytest_lsp import check
from pytest_lsp import Client

from esbonio.lsp.testing import completion_request

EXPECTED = {
    "autoclass",
    "automodule",
    "py:function",
    "py:module",
    "option",
    "program",
    "image",
    "toctree",
    "macro",
    "not-a-true-directive",  # Ensure the server doesn't crash on non-standard directives.
    "function",
}

UNEXPECTED = {
    "c:macro",
    "module",
    "std:program",
    "std:option",
    "restructuredtext-test-directive",
}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "text,expected,unexpected",
    [
        (".", None, None),
        ("..", EXPECTED, UNEXPECTED),
        (".. ", EXPECTED, UNEXPECTED),
        (".. d", EXPECTED, UNEXPECTED),
        (".. code-b", EXPECTED, UNEXPECTED),
        (".. codex-block:: ", None, None),
        (".. _some_label:", None, None),
        (
            ".. py:",
            {"py:function", "py:module"},
            {"image", "toctree", "macro", "function"},
        ),
        (".. c:", None, None),
        ("   .", None, None),
        ("   ..", EXPECTED, UNEXPECTED),
        ("   .. ", EXPECTED, UNEXPECTED),
        ("   .. d", EXPECTED, UNEXPECTED),
        ("   .. doctest:: ", None, None),
        ("   .. code-b", EXPECTED, UNEXPECTED),
        ("   .. codex-block:: ", None, None),
        ("   .. _some_label:", None, None),
        (
            "   .. py:",
            {"py:function", "py:module"},
            {"image", "toctree", "macro", "function"},
        ),
        ("   .. c:", None, None),
    ],
)
async def test_directive_completions(
    client: Client,
    text: str,
    expected: Optional[Set[str]],
    unexpected: Optional[Set[str]],
):

    test_uri = client.root_uri + "/test.rst"
    results = await completion_request(client, test_uri, text)

    items = {item.label for item in results.items}
    expected = expected or set()
    unexpected = unexpected or set()

    assert expected == items & expected
    assert set() == items & unexpected

    check.completion_items(client, results.items)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "text,label,expected",
    [
        (
            "..",
            "function",
            "Describes a C function. The signature",
        ),
        (
            "..",
            "py:function",
            "Describes a module-level function.  The signature",
        ),
    ],
)
async def test_directive_completion_resolve(
    client: Client, text: str, label: str, expected: str
):
    """Ensure that we handle ``completionItem/resolve`` requests correctly.

    This test case is focused on filling out additional fields of a ``CompletionItem``
    that is selected in some language client.

    Cases are parameterized with the inputs are expected to have the following format::

       (".. example::", "example", "## Example")

    where:

    - ``.. example::`` is the text used when making the initial
      ``textDocument/completion`` request
    - ``example`` is the label of the ``CompletionItem`` we want to "select".
    - ``## Example`` is the expected documentation we want to test for.

    Parameters
    ----------
    client:
       The client fixture used to drive the test
    text:
       The text providing the context of the completion request
    label:
       The label of the ``CompletionItem`` to select
    expected:
       The documentation to look for, will be passed to :func:`python:str.startswith`
    """

    test_uri = client.root_uri + "/test.rst"

    results = await completion_request(client, test_uri, text)
    items = {item.label: item for item in results.items}

    assert label in items, f"Missing expected CompletionItem {label}"
    item = items[label]

    # Server should not be filling out docs by default
    assert item.documentation is None, "Unexpected documentation text."

    item = await client.completion_resolve_request(item)
    assert item.documentation.kind == MarkupKind.Markdown
    assert item.documentation.value.startswith(expected)


AUTOCLASS_OPTS = {
    "members",
    "undoc-members",
    "noindex",
    "inherited-members",
    "show-inheritance",
    "member-order",
    "exclude-members",
    "private-members",
    "special-members",
}
IMAGE_OPTS = {"align", "alt", "class", "height", "scale", "target", "width"}
PY_FUNC_OPTS = {"annotation", "async", "module", "noindex"}
C_FUNC_OPTS = {"noindexentry"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "text, expected, unexpected",
    [
        (".. image:: f.png\n\f   :", IMAGE_OPTS, {"ref", "func"}),
        (
            ".. function:: foo\n\f   :",
            C_FUNC_OPTS,
            {"ref", "func"},
        ),
        (
            ".. py:function:: foo\n\f   :",
            PY_FUNC_OPTS,
            {"ref", "func"},
        ),
        (
            ".. autoclass:: x.y.A\n\f   :",
            AUTOCLASS_OPTS,
            {"ref", "func"},
        ),
        (
            "   .. image:: f.png\n\f      :",
            IMAGE_OPTS,
            {"ref", "func"},
        ),
        (
            "   .. function:: foo\n\f      :",
            C_FUNC_OPTS,
            {"ref", "func"},
        ),
        (
            "   .. autoclass:: x.y.A\n\f      :",
            AUTOCLASS_OPTS,
            {"ref", "func"},
        ),
    ],
)
async def test_directive_option_completions(
    client: Client,
    text: str,
    expected: Optional[Set[str]],
    unexpected: Optional[Set[str]],
):

    test_uri = client.root_uri + "/test.rst"
    results = await completion_request(client, test_uri, text)

    items = {item.label for item in results.items}
    expected = expected or set()
    unexpected = unexpected or set()

    assert expected == items & expected
    assert set() == items & unexpected

    check.completion_items(client, results.items)
