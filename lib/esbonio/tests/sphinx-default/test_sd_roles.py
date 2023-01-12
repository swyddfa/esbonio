import itertools
import pathlib
import re
from typing import Optional
from typing import Set
from typing import Tuple

import pytest
from lsprotocol.types import Position
from lsprotocol.types import Range
from pytest_lsp import LanguageClient
from pytest_lsp import check

from esbonio.lsp.testing import completion_request
from esbonio.lsp.testing import hover_request
from esbonio.lsp.testing import role_patterns
from esbonio.lsp.testing import sphinx_version

C_EXPECTED = {"c:func", "c:macro"}
C_UNEXPECTED = {"restructuredtext-unimplemented-role"}

EXPECTED = {"doc", "func", "mod", "ref", "c:func"}
UNEXPECTED = {"restructuredtext-unimplemented-role"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "text,setup",
    [
        *itertools.product(
            role_patterns(":") + role_patterns(":r") + role_patterns(":ref:"),
            [(EXPECTED, UNEXPECTED)],
        ),
        *itertools.product(
            role_patterns("a:") + role_patterns("figure::"),
            [(None, None)],
        ),
        *itertools.product(
            role_patterns(":py:"),
            [(EXPECTED, UNEXPECTED)],
        ),
        *itertools.product(
            role_patterns(":c:"),
            [(C_EXPECTED, C_UNEXPECTED)],
        ),
    ],
)
async def test_role_completions(
    client: LanguageClient,
    text: str,
    setup: Tuple[str, Optional[Set[str]], Optional[Set[str]]],
):
    """Ensure that we can offer correct role suggestions.

    This test case is focused on the list of completion items we return for a
    given completion request. This ensures we correctly handle differing sphinx
    configurations and extensions while discovering the available roles.

    Cases are parameterized and the inputs are expected to have the following format::

       ("more info :", ({'expected'}, {'unexpected'}))

    where:

    - ``{'expected'}`` is the set of completion item labels you expect to see returned
      from the completion request. Can be ``None`` which will assert that no completions
      are returned.
    - ``{'unexpected'}`` is the set of completion item labels you **do not** expect to
      see returned from the completion request.

    A common pattern where a number of different values for ``text`` should produce the
    same set of results within a given setup, is to make use of
    :func:`python:itertools.product` to generate all combinations of setups.

    Parameters
    ----------
    client:
       The client fixture used to drive the test.
    text:
       The text providing the context of the completion request.
    setup:
       The tuple providing the rest of the setup for the test.
    """

    expected, unexpected = setup
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
    "text,character,expected_range",
    [
        (
            ":ref",
            None,
            Range(
                start=Position(line=0, character=0), end=Position(line=0, character=4)
            ),
        ),
        (
            "some :ref",
            None,
            Range(
                start=Position(line=0, character=5), end=Position(line=0, character=9)
            ),
        ),
        (
            ":ref:",
            None,
            Range(
                start=Position(line=0, character=0), end=Position(line=0, character=5)
            ),
        ),
        (
            ":c:func",
            None,
            Range(
                start=Position(line=0, character=0), end=Position(line=0, character=7)
            ),
        ),
        (
            ":c:func:",
            None,
            Range(
                start=Position(line=0, character=0), end=Position(line=0, character=8)
            ),
        ),
        (
            ":func:`some_func`",
            5,
            Range(
                start=Position(line=0, character=0), end=Position(line=0, character=6)
            ),
        ),
    ],
)
async def test_role_insert_range(
    client: LanguageClient, text: str, character: int, expected_range: Range
):
    """Ensure that we generate completion items that work well with existing text.

    This test case is focused on the range of text a ``CompletionItem`` will modify if
    selected. This is to ensure that we don't create more work for the end user by
    corrupting the line we edit, or leaving additional characters that are not
    required.

    Cases are parameterized and the inputs are expected to have the following format::

       ("some :ref", 7, Range(...))

    where:

    - ``"some :ref"`` corresponds to the text to insert into the test file.
    - ``7`` is the character index to trigger the completion request at.
    - ``Range(...)`` the expected range the resulting ``CompletionItems`` should modify

    Parameters
    ----------
    client:
       The client fixure used to drive the test.
    project:
       The name of the Sphinx project to use as listed in the ``tests/data`` folder.
    text:
       The text providing the context for the completion request
    character:
       The index at which to make the completion request, if ``None`` it will default
       to the end of the line.
    expected_range:
       The range the resulting ``CompletionItems`` should modify.
    """

    test_uri = client.root_uri + "/test.rst"

    results = await completion_request(client, test_uri, text, character=character)
    assert len(results.items) > 0

    for item in results.items:
        assert item.text_edit.range == expected_range
        assert item.text_edit.new_text.endswith(":")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "extension,setup",
    [
        *itertools.product(
            ["rst"],
            [
                (":", True, None),
                (":ref:`", True, None),
                (":ref:`some text <example>`", True, 17),
                (":ref:`some text <example>`", False, 6),
            ],
        ),
        *itertools.product(
            ["py"],
            [
                (":", False, None),
                (":ref:`", False, None),
                ('""":', True, None),
                ('"""\n\f:', True, None),
                ('""":ref:`', True, None),
                ('"""\na docstring.\n"""\n\f:', False, None),
                ('"""\na docstring.\n"""\n\f:ref:`', False, None),
            ],
        ),
    ],
)
async def test_completion_suppression(client: LanguageClient, extension: str, setup):
    """Ensure that we only offer completions when appropriate.

    Rather than focus on the actual completion items themselves, this test case is
    concerned with ensuring that role suggestions are only offered at an appropriate
    time e.g. within ``*.rst`` files and docstrings and not within python code.

    Cases are parameterized and inputs are expected to have the following format::

       ("rst", ":ref", True, 1)

    where:

    - ``"rst"`` corresponds to the file extension of the file the completion request
      should be made from.
    - ``":ref"`` is the text that provides the context of the completion request
    - ``True`` is a flag that indicates if we expect to see completion suggestions
      generated or not.
    - ``12`` is used to indicate the character index the completion request should
      be made from. If ``None`` the request will default to the end of the given text.

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
    "text,line,character,expected",
    [
        (
            ":option:`progname.--verbose`",
            0,
            4,
            "A command-line option",
        ),
        (
            ":option:`progname.--verbose`",
            0,
            12,
            None,
        ),
        (
            ":not-a-known-role:`progname.--verbose`",
            0,
            4,
            None,
        ),
        (
            ":c:expr:",
            0,
            1,
            "Insert a C expression or type",
        ),
    ],
)
async def test_role_hovers(
    client: LanguageClient,
    text: str,
    line: int,
    character: int,
    expected: Optional[str],
):
    """Ensure that we can offer hovers for roles correctly."""

    test_uri = client.root_uri + "/test.rst"

    hover = await hover_request(client, test_uri, text, line, character)
    actual = hover.contents.value

    if expected is None:
        assert actual == ""
    else:
        assert actual.startswith(expected)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "text,pattern,expected_range",
    [
        (
            ":ref:`some_text",
            ".*`",
            Range(
                start=Position(line=0, character=6), end=Position(line=0, character=15)
            ),
        ),
        (
            ":ref:`!some_text",
            "!.*`",
            Range(
                start=Position(line=0, character=6), end=Position(line=0, character=16)
            ),
        ),
        (
            ":ref:`~some_text",
            "~.*`",
            Range(
                start=Position(line=0, character=6), end=Position(line=0, character=16)
            ),
        ),
        (
            "find out more :ref:`some_text",
            ".*`",
            Range(
                start=Position(line=0, character=20), end=Position(line=0, character=29)
            ),
        ),
        (
            ":ref:`more info <some_text",
            ".*>`",
            Range(
                start=Position(line=0, character=17), end=Position(line=0, character=26)
            ),
        ),
        (
            ":ref:`more info <!some_text",
            "!.*>`",
            Range(
                start=Position(line=0, character=17), end=Position(line=0, character=27)
            ),
        ),
        (
            ":ref:`more info <~some_text",
            "~.*>`",
            Range(
                start=Position(line=0, character=17), end=Position(line=0, character=27)
            ),
        ),
        (
            ":download:`_static/vscode_screenshot.png",
            ".*`",
            Range(
                start=Position(line=0, character=19), end=Position(line=0, character=40)
            ),
        ),
        (
            ":download:`this link <_static/vscode_screenshot.png",
            ".*>`",
            Range(
                start=Position(line=0, character=30), end=Position(line=0, character=51)
            ),
        ),
    ],
)
async def test_role_target_insert_range(
    client: LanguageClient, text: str, pattern: str, expected_range: Range
):
    """Ensure that we generate completion items that work well with existing text.

    This test case is focused on the ``TextEdit`` objects returned as part of a
    ``CompletionItem``. They need to take into account any existing text so that if an
    item is accepted, the user is not forced to do additonal cleanups.

    The test case is parameterised.

    Parameters
    ----------
    client:
       The client fixture used to drive the test
    text:
       The text that provides the context for the completion request e.g.
       ``:ref:`label``
    pattern:
       A regular expression used to check the value of the ``new_text`` field of
       returned ``TextEdits``
    expected_range:
       A ``Range`` object to check the value of the ``range`` field of returned
       ``TextEdits``
    """

    test_uri = client.root_uri + "/test.rst"
    pattern = re.compile(pattern)

    results = await completion_request(client, test_uri, text)
    assert len(results.items) > 0

    for item in results.items:
        assert pattern.match(item.text_edit.new_text) is not None
        assert item.text_edit.range == expected_range


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "uri,line,character,expected",
    [
        (
            "definitions.rst",
            5,
            34,
            None,
        ),
        (
            "definitions.rst",
            5,
            27,
            "sphinx/roles.py",
        ),
        (
            "definitions.rst",
            33,
            21,
            "sphinx/domains/cpp.py",
        ),
        pytest.param(
            "theorems/pythagoras.rst",
            50,
            19,
            "docutils/parsers/rst/roles.py",
            marks=pytest.mark.skipif(
                sphinx_version(gte=5),
                reason=":code: is provided by docutils up to and including Sphinx 4.x",
            ),
        ),
        pytest.param(
            "theorems/pythagoras.rst",
            50,
            19,
            "sphinx/roles.py",
            marks=pytest.mark.skipif(
                sphinx_version(lt=5),
                reason=":code: is provided by Sphinx from v5.x ",
            ),
        ),
    ],
)
async def test_roles_implementation(
    client: LanguageClient,
    uri: str,
    line: int,
    character: int,
    expected: Optional[pathlib.Path],
):
    """Ensure that we can find the implementation of roles.

    Since we're testing items provided by 3rd party packages (Sphinx + docutils) we can't
    really check the precise location as tests could break each time a new version is
    released.

    Instead let's go for just the containing file and hope the rest is correct!
    """

    test_uri = client.root_uri + f"/{uri}"

    results = await client.implementation_request(test_uri, line, character)

    if expected is None:
        assert len(results) == 0

    else:
        assert len(results) == 1

        location = results[0]
        assert location.uri.endswith(str(expected))
        assert location.range.start.line >= 0
        assert location.range.end.line > location.range.start.line
