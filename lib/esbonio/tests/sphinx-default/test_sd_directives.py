import itertools
from typing import Optional
from typing import Set

import pytest
from pygls.lsp.types import MarkupKind
from pygls.lsp.types import Position
from pygls.lsp.types import Range
from pytest_lsp import check
from pytest_lsp import Client

from esbonio.lsp.testing import completion_request
from esbonio.lsp.testing import hover_request
from esbonio.lsp.testing import sphinx_version

EXPECTED = {
    "function",
    "module",
    "option",
    "program",
    "image",
    "toctree",
    "c:macro",
    "c:function",
}

UNEXPECTED = {
    "autoclass",
    "automodule",
    "py:function",
    "py:module",
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
        (".. py:", None, None),
        (".. c:", {"c:macro", "c:function"}, {"function", "image", "toctree"}),
        (".. _some_label:", None, None),
        ("   .", None, None),
        ("   ..", EXPECTED, UNEXPECTED),
        ("   .. ", EXPECTED, UNEXPECTED),
        ("   .. d", EXPECTED, UNEXPECTED),
        ("   .. doctest:: ", None, None),
        ("   .. code-b", EXPECTED, UNEXPECTED),
        ("   .. codex-block:: ", None, None),
        ("   .. py:", None, None),
        ("   .. _some_label:", None, None),
        ("   .. c:", {"c:macro", "c:function"}, {"function", "image", "toctree"}),
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
        ("..", "compound", "## Compound Paragraph"),
        ("..", "toctree", 'This directive inserts a "TOC tree" at'),
        (
            "..",
            "function",
            "Describes a module-level function.  The signature",
        ),
        pytest.param(
            ".. function:: foo\n   \f:",
            "async",
            "Describes a module-level function.  The signature",
            marks=pytest.mark.xfail(
                reason="generate_sphinx_documentation.py doesn't extract options yet."
            ),
        ),
        pytest.param(
            "..",
            "c:function",
            "Describes a C function. The signature",
            marks=pytest.mark.skipif(sphinx_version(eq=2), reason="Sphinx 2.x"),
        ),
        (
            ".. image:: filename.png\n   \f:",
            "align",
            '"top", "middle", "bottom"',
        ),
        pytest.param(
            ".. py:function:: foo\n   \f:",
            "async",
            "Describes a module-level function.  The signature",
            marks=pytest.mark.xfail(
                reason="generate_sphinx_documentation.py doesn't extract options yet."
            ),
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
C_FUNC_OPTS = {"noindex"} if sphinx_version(eq=2) else {"noindexentry"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "text, expected, unexpected",
    [
        (".. image:: f.png\n\f   :", IMAGE_OPTS, {"ref", "func"}),
        (
            ".. image:: f.png\n   :align:\n\f   :",
            IMAGE_OPTS,
            {"ref", "func"},
        ),
        (".. function:: foo\n\f   :", PY_FUNC_OPTS, {"ref", "func"}),
        (
            ".. autoclass:: x.y.A\n\f   :",
            set(),
            {"ref", "func"} | AUTOCLASS_OPTS,
        ),
        (
            "   .. image:: f.png\n\f      :",
            IMAGE_OPTS,
            {"ref", "func"},
        ),
        (
            "   .. function:: foo\n\f      :",
            PY_FUNC_OPTS,
            {"ref", "func"},
        ),
        (
            "   .. c:function:: foo\n\f      :",
            C_FUNC_OPTS,
            {"ref", "func"},
        ),
        (
            "   .. autoclass:: x.y.A\n\f      :",
            set(),
            {"ref", "func"} | AUTOCLASS_OPTS,
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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "extension,setup",
    [
        *itertools.product(
            ["rst"],
            [
                ("..", True, None),
                (".. image:: ", True, None),
                (".. image:: filename.png\n   \f:", True, None),
                (".. image:: filename.png\n\f   :align", False, 1),
                (".. image:: filename.png\n\f   :align", True, 5),
                (".. image:: filename.png\n\f   :align:", True, 5),
                (".. image:: filename.png\n\f   :align: center", False, 12),
            ],
        ),
        *itertools.product(
            ["py"],
            [
                ("..", False, None),
                (".. image:: ", False, None),
                (".. image:: filename.png\n   \f:", False, None),
                ('"""\n\f..', True, None),
                ('"""\n\f.. image:: ', True, None),
                ('"""\n.. image:: filename.png\n   \f:', True, None),
            ],
        ),
    ],
)
async def test_completion_suppression(client: Client, extension: str, setup):
    """Ensure that we only offer completions when appropriate.

    Rather than focus on the actual completion items themselves, this test case is
    concerned with ensuring that role suggestions are only offered at an appropriate
    time e.g. within ``*.rst`` files and docstrings and not within python code.

    Cases are parameterized and inputs are expected to have the following format::

       ("rst", "   :align:", False, 1)

    where:

    - ``"rst"`` corresponds to the file extension of the file the completion request
      should be made from.
    - ``"   :align:"`` is the text that provides the context of the completion request
    - ``False`` is a flag that indicates if we expect to see completion suggestions
      generated or not.
    - ``1`` is used to indicate the character index the completion request should be
      made from. If ``None`` the request will default to the end of the given text.

    A common pattern for when multiple test cases are paired with the same file
    extension is to make use of :func:`python:itertools.product` to "broadcast" the
    file extension across a number of setups.
    """

    test_uri = client.root_uri + f"/test.{extension}"

    text, expected, character = setup

    results = await completion_request(client, test_uri, text, character=character)
    assert (len(results.items) > 0) == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "text,position,expected",
    [
        (
            ".. deprecated:: 0.12.0",
            Position(line=0, character=4),
            "Similar to [versionchanged]",
        ),
        (
            ".. deprecated:: 0.12.0",
            Position(line=0, character=16),
            None,
        ),
        (
            ".. not-a-known-directive:: ",
            Position(line=0, character=4),
            None,
        ),
        pytest.param(
            ".. c:function:: ",
            Position(line=0, character=1),
            "Describes a C function",
            marks=pytest.mark.skipif(sphinx_version(eq=2), reason="Sphinx 2.x"),
        ),
    ],
)
async def test_directive_hovers(
    client: Client, text: str, position: Position, expected: Optional[str]
):
    """Ensure that we can offer hovers for directives correctly."""

    test_uri = client.root_uri + "/test.rst"

    hover = await hover_request(client, test_uri, text, position)
    actual = hover.contents.value

    if expected is None:
        assert actual == ""
    else:
        assert actual.startswith(expected)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "text,character,expected_range",
    [
        (
            "..",
            None,
            Range(
                start=Position(line=0, character=0), end=Position(line=0, character=2)
            ),
        ),
        (
            ".. function",
            None,
            Range(
                start=Position(line=0, character=0), end=Position(line=0, character=11)
            ),
        ),
        (
            ".. function::",
            3,
            Range(
                start=Position(line=0, character=0), end=Position(line=0, character=13)
            ),
        ),
        (
            ".. function::\n\f   :",
            4,
            Range(
                start=Position(line=1, character=3), end=Position(line=1, character=4)
            ),
        ),
        (
            ".. function::\n\f   :align",
            4,
            Range(
                start=Position(line=1, character=3), end=Position(line=1, character=9)
            ),
        ),
        (
            ".. function::\n\f   :align: center",
            4,
            Range(
                start=Position(line=1, character=3), end=Position(line=1, character=10)
            ),
        ),
    ],
)
async def test_insert_range(
    client: Client, text: str, character: int, expected_range: Range
):
    """Ensure that we generate completion items that work well with existing text.

    This test case is focused on the range of text a ``CompletionItem`` will modify
    if selected. This is to ensure that we don't create more work for the end user by
    corrupting the line we edit or leaving additional characters that are not required.

    Cases are parameterized and the inputs are expected to have the following format::

       (".. image", 3, Range(...))

    where:

    - ``".. image"`` corresponds to the text to insert into the test file
    - ``7`` is the character index to trigger the completion request at. If ``None`` it
      will default to the end of the line
    - ``Range(...)`` is the expected range the resulting ``CompletionItem`` should
      modify
    """

    test_uri = client.root_uri + "/test.rst"

    results = await completion_request(client, test_uri, text, character=character)
    assert len(results.items) > 0

    for item in results.items:
        assert item.text_edit.range == expected_range
