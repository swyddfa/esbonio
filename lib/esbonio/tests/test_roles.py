import itertools
from typing import Optional
from typing import Set
from typing import Tuple

import py.test
from pygls.lsp.types import Location
from pygls.lsp.types import Position
from pygls.lsp.types import Range

from esbonio.lsp.roles import ROLE
from esbonio.lsp.testing import ClientServer
from esbonio.lsp.testing import completion_request
from esbonio.lsp.testing import definition_request
from esbonio.lsp.testing import intersphinx_target_patterns
from esbonio.lsp.testing import role_patterns
from esbonio.lsp.testing import role_target_patterns

C_EXPECTED = {"c:func", "c:macro"}
C_UNEXPECTED = {"py:func", "py:mod"}

DEFAULT_EXPECTED = {"doc", "func", "mod", "ref", "c:func"}
DEFAULT_UNEXPECTED = {"py:func", "py:mod", "restructuredtext-unimplemented-role"}

EXT_EXPECTED = {"doc", "py:func", "py:mod", "ref", "func"}
EXT_UNEXPECTED = {"c:func", "c:macro", "restructuredtext-unimplemented-role"}

PY_EXPECTED = {"py:func", "py:mod"}
PY_UNEXPECTED = {"c:func", "c:macro"}


@py.test.mark.asyncio
@py.test.mark.parametrize(
    "text,setup",
    [
        *itertools.product(
            role_patterns(":") + role_patterns(":r") + role_patterns(":ref:"),
            [
                ("sphinx-default", DEFAULT_EXPECTED, DEFAULT_UNEXPECTED),
                ("sphinx-extensions", EXT_EXPECTED, EXT_UNEXPECTED),
            ],
        ),
        *itertools.product(
            role_patterns("a:") + role_patterns("figure::"),
            [("sphinx-default", None, None), ("sphinx-extensions", None, None)],
        ),
        *itertools.product(
            role_patterns(":py:"),
            [
                ("sphinx-default", DEFAULT_EXPECTED, DEFAULT_UNEXPECTED),
                ("sphinx-extensions", PY_EXPECTED, PY_UNEXPECTED),
            ],
        ),
        *itertools.product(
            role_patterns(":c:"),
            [
                ("sphinx-default", C_EXPECTED, C_UNEXPECTED),
                ("sphinx-extensions", EXT_EXPECTED, EXT_UNEXPECTED),
            ],
        ),
    ],
)
async def test_role_completions(
    client_server: ClientServer,
    text: str,
    setup: Tuple[str, Optional[Set[str]], Optional[Set[str]]],
):
    """Ensure that we can offer correct role suggestions.

    This test case is focused on the list of completion items we return for a
    given completion request. This ensures we correctly handle differing sphinx
    configurations and extensions while discovering the available roles.

    Cases are parameterized and the inputs are expected to have the following format::

       ("more info :", ("sphinx-project", {'expected'}, {'unexpected'}))

    where:

    - ``"sphinx-project"`` corresponds to the name of one of the example Sphinx projects
      in the ``tests/data/`` folder.
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
    client_server:
       The client_server fixture used to drive the test.
    text:
       The text providing the context of the completion request.
    setup:
       The tuple providing the rest of the setup for the test.
    """

    project, expected, unexpected = setup

    test = await client_server(project)
    test_uri = test.server.workspace.root_uri + "/test.rst"

    results = await completion_request(test, test_uri, text)

    items = {item.label for item in results.items}
    unexpected = unexpected or set()

    if expected is None:
        assert len(items) == 0
    else:
        assert expected == items & expected
        assert set() == items & unexpected


@py.test.mark.asyncio
@py.test.mark.parametrize(
    "project,text,character,expected_range",
    [
        (
            "sphinx-default",
            ":ref",
            None,
            Range(
                start=Position(line=0, character=0), end=Position(line=0, character=4)
            ),
        ),
        (
            "sphinx-default",
            "some :ref",
            None,
            Range(
                start=Position(line=0, character=5), end=Position(line=0, character=9)
            ),
        ),
        (
            "sphinx-default",
            ":ref:",
            None,
            Range(
                start=Position(line=0, character=0), end=Position(line=0, character=5)
            ),
        ),
        (
            "sphinx-default",
            ":c:func",
            None,
            Range(
                start=Position(line=0, character=0), end=Position(line=0, character=7)
            ),
        ),
        (
            "sphinx-default",
            ":c:func:",
            None,
            Range(
                start=Position(line=0, character=0), end=Position(line=0, character=8)
            ),
        ),
        (
            "sphinx-default",
            ":func:`some_func`",
            5,
            Range(
                start=Position(line=0, character=0), end=Position(line=0, character=6)
            ),
        ),
    ],
)
async def test_role_insert_range(
    client_server, project, text, character, expected_range
):
    """Ensure that we generate completion items that work well with existing text.

    This test case is focused on the range of text a ``CompletionItem`` will modify if
    selected. This is to ensure that we don't create more work for the end user by
    corrupting the line we edit, or leaving additional characters that are not
    required.

    Cases are parameterized and the inputs are expected to have the following format::

       ("sphinx-default", "some :ref", 7, Range(...))

    where:

    - ``"sphinx-default"`` corresponds to the Sphinx project to execute the test case
      within.
    - ``"some :ref"`` corresponds to the text to insert into the test file.
    - ``7`` is the character index to trigger the completion request at.
    - ``Range(...)`` the expected range the resulting ``CompletionItems`` should modify

    Parameters
    ----------
    client_server:
       The ``client_server`` fixure used to drive the test.
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

    test = await client_server(project)  # type: ClientServer
    test_uri = test.server.workspace.root_uri + "/test.rst"

    results = await completion_request(test, test_uri, text, character=character)
    assert len(results.items) > 0

    for item in results.items:
        assert item.text_edit.range == expected_range
        assert item.text_edit.new_text.endswith(":")


@py.test.mark.asyncio
@py.test.mark.parametrize(
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
async def test_completion_suppression(client_server, extension, setup):
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

    test = await client_server("sphinx-default")
    test_uri = test.server.workspace.root_uri + f"/test.{extension}"

    print(extension, setup)
    text, expected, character = setup

    results = await completion_request(test, test_uri, text, character=character)
    assert (len(results.items) > 0) == expected


WELCOME_LABEL = Location(
    uri="index.rst",
    range=Range(
        start=Position(line=5, character=0),
        end=Position(line=6, character=0),
    ),
)


@py.test.mark.asyncio
@py.test.mark.parametrize(
    "project,path,position,expected",
    [
        ("sphinx-default", "definitions.rst", Position(line=3, character=33), None),
        ("sphinx-default", "definitions.rst", Position(line=5, character=13), None),
        ("sphinx-default", "definitions.rst", Position(line=7, character=33), None),
        ("sphinx-default", "definitions.rst", Position(line=9, character=42), None),
        (
            "sphinx-default",
            "definitions.rst",
            Position(line=5, character=33),
            WELCOME_LABEL,
        ),
        (
            "sphinx-default",
            "definitions.rst",
            Position(line=9, character=35),
            WELCOME_LABEL,
        ),
        (
            "sphinx-default",
            "definitions.rst",
            Position(line=11, character=28),
            WELCOME_LABEL,
        ),
        (
            "sphinx-default",
            "definitions.rst",
            Position(line=11, character=35),
            WELCOME_LABEL,
        ),
        (
            "sphinx-default",
            "definitions.rst",
            Position(line=9, character=56),
            Location(
                uri="theorems/pythagoras.rst",
                range=Range(
                    start=Position(line=0, character=0),
                    end=Position(line=1, character=0),
                ),
            ),
        ),
        (
            "sphinx-default",
            "definitions.rst",
            Position(line=13, character=36),
            Location(
                uri="changelog.rst",
                range=Range(
                    start=Position(line=0, character=0),
                    end=Position(line=1, character=0),
                ),
            ),
        ),
    ],
)
async def test_role_target_definitions(
    client_server, project, path, position, expected
):
    """Ensure that we can offer the correct definitions for role targets."""

    test = await client_server(project)
    test_uri = test.server.workspace.root_uri + f"/{path}"

    results = await definition_request(test, test_uri, position)

    if expected is None:
        assert len(results) == 0
    else:
        assert len(results) == 1
        result = results[0]

        assert result.uri == test.server.workspace.root_uri + f"/{expected.uri}"
        assert result.range == expected.range


@py.test.mark.asyncio
@py.test.mark.parametrize(
    "text,setup",
    [
        # Standard domain
        *itertools.product(
            role_target_patterns("doc"),
            [
                (
                    "sphinx-default",
                    {"index", "glossary", "theorems/index", "theorems/pythagoras"},
                    None,
                )
            ],
        ),
        *itertools.product(
            role_target_patterns("ref"),
            [
                (
                    "sphinx-default",
                    {
                        "genindex",
                        "modindex",
                        "pythagoras_theorem",
                        "search",
                        "welcome",
                    },
                    None,
                )
            ],
        ),
        *itertools.product(
            intersphinx_target_patterns("ref", "python"),
            [
                (
                    "sphinx-default",
                    set(),
                    {"configparser-objects", "types", "whatsnew-index"},
                ),
                (
                    "sphinx-extensions",
                    {"configparser-objects", "types", "whatsnew-index"},
                    set(),
                ),
            ],
        ),
        *itertools.product(
            intersphinx_target_patterns("ref", "sphinx"),
            [
                (
                    "sphinx-default",
                    set(),
                    {
                        "basic-domain-markup",
                        "extension-tutorials-index",
                        "writing-builders",
                    },
                ),
                (
                    "sphinx-extensions",
                    {
                        "basic-domain-markup",
                        "extension-tutorials-index",
                        "writing-builders",
                    },
                    set(),
                ),
            ],
        ),
        # Python Domain
        *itertools.product(
            role_target_patterns("class"),
            [
                ("sphinx-default", {"pythagoras.Triangle"}, None),
                ("sphinx-extensions", {"python", "sphinx"}, {"pythagoras.Triangle"}),
            ],
        ),
        *itertools.product(
            role_target_patterns("func"),
            [
                (
                    "sphinx-default",
                    {"pythagoras.calc_hypotenuse", "pythagoras.calc_side"},
                    None,
                ),
                (
                    "sphinx-extensions",
                    {"sphinx", "python"},
                    {"pythagoras.calc_hypotenuse", "pythagoras.calc_side"},
                ),
            ],
        ),
        *itertools.product(
            intersphinx_target_patterns("func", "python"),
            [
                (
                    "sphinx-default",
                    set(),
                    {"_Py_c_sum", "PyErr_Print", "PyUnicode_Count"},
                ),
                (
                    "sphinx-extensions",
                    {"_Py_c_sum", "PyErr_Print", "PyUnicode_Count"},
                    set(),
                ),
            ],
        ),
        *itertools.product(
            role_target_patterns("py:func"),
            [
                (
                    "sphinx-default",
                    None,
                    {"pythagoras.calc_hypotenuse", "pythagoras.calc_side"},
                ),
                (
                    "sphinx-extensions",
                    {
                        "pythagoras.calc_hypotenuse",
                        "pythagoras.calc_side",
                        "python",
                        "sphinx",
                    },
                    None,
                ),
            ],
        ),
        *itertools.product(
            intersphinx_target_patterns("py:func", "python"),
            [
                (
                    "sphinx-default",
                    set(),
                    {"abc.abstractmethod", "msvcrt.locking", "types.new_class"},
                ),
                (
                    "sphinx-extensions",
                    {"abc.abstractmethod", "msvcrt.locking", "types.new_class"},
                    set(),
                ),
            ],
        ),
        *itertools.product(
            role_target_patterns("meth"),
            [
                ("sphinx-default", {"pythagoras.Triangle.is_right_angled"}, None),
                (
                    "sphinx-extensions",
                    {"sphinx", "python"},
                    {"pythagoras.Triangle.is_right_angled"},
                ),
            ],
        ),
        *itertools.product(
            role_target_patterns("py:meth"),
            [
                ("sphinx-default", None, {"pythagoras.Triangle.is_right_angled"}),
                (
                    "sphinx-extensions",
                    {"sphinx", "python", "pythagoras.Triangle.is_right_angled"},
                    None,
                ),
            ],
        ),
        *itertools.product(
            role_target_patterns("obj"),
            [
                (
                    "sphinx-default",
                    {
                        "pythagoras",
                        "pythagoras.PI",
                        "pythagoras.UNKNOWN",
                        "pythagoras.Triangle",
                        "pythagoras.Triangle.a",
                        "pythagoras.Triangle.b",
                        "pythagoras.Triangle.c",
                        "pythagoras.Triangle.is_right_angled",
                        "pythagoras.calc_hypotenuse",
                        "pythagoras.calc_side",
                    },
                    None,
                ),
                (
                    "sphinx-extensions",
                    {"sphinx", "python"},
                    {
                        "pythagoras",
                        "pythagoras.PI",
                        "pythagoras.UNKNOWN",
                        "pythagoras.Triangle",
                        "pythagoras.Triangle.a",
                        "pythagoras.Triangle.b",
                        "pythagoras.Triangle.c",
                        "pythagoras.Triangle.is_right_angled",
                        "pythagoras.calc_hypotenuse",
                        "pythagoras.calc_side",
                    },
                ),
            ],
        ),
        *itertools.product(
            role_target_patterns("py:obj"),
            [
                (
                    "sphinx-extensions",
                    {
                        "pythagoras",
                        "pythagoras.PI",
                        "pythagoras.UNKNOWN",
                        "pythagoras.Triangle",
                        "pythagoras.Triangle.a",
                        "pythagoras.Triangle.b",
                        "pythagoras.Triangle.c",
                        "pythagoras.Triangle.is_right_angled",
                        "pythagoras.calc_hypotenuse",
                        "pythagoras.calc_side",
                        "python",
                        "sphinx",
                    },
                    None,
                ),
                (
                    "sphinx-default",
                    None,
                    {
                        "pythagoras",
                        "pythagoras.PI",
                        "pythagoras.UNKNOWN",
                        "pythagoras.Triangle",
                        "pythagoras.Triangle.a",
                        "pythagoras.Triangle.b",
                        "pythagoras.Triangle.c",
                        "pythagoras.Triangle.is_right_angled",
                        "pythagoras.calc_hypotenuse",
                        "pythagoras.calc_side",
                    },
                ),
            ],
        ),
        *itertools.product(
            role_target_patterns("option"),
            [
                (
                    "sphinx-default",
                    {
                        "pythag -e",
                        "pythag --exact",
                        "pythag -u",
                        "pythag --unit",
                        "pythag -p",
                        "pythag --precision",
                    },
                    None,
                )
            ],
        ),
    ],
)
async def test_role_target_completions(client_server, text, setup):
    """Ensure that we can offer correct role target suggestions.

    This test case is focused on the list of completion items we return for a
    given completion request. This ensures we correctly handle differing sphinx
    configurations and extensions while discovering the available roles.

    Cases are parameterized and the inputs are expected to have the following format::

       (":ref:`", ("sphinx-project", {'expected'}, {'unexpected'}))

    where:

    - ``"sphinx-project"`` corresponds to the name of one of the example Sphinx projects
      in the ``tests/data/`` folder.
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
    client_server:
       The client_server fixture used to drive the test.
    text:
       The text providing the context of the completion request.
    setup:
       The tuple providing the rest of the setup for the test.
    """

    project, expected, unexpected = setup

    test = await client_server(project)
    test_uri = test.server.workspace.root_uri + "/test.rst"

    results = await completion_request(test, test_uri, text)

    items = {item.label for item in results.items}
    unexpected = unexpected or set()

    if expected is None:
        assert len(items) == 0
    else:
        assert expected == items & expected
        assert set() == items & unexpected


@py.test.mark.asyncio
@py.test.mark.parametrize(
    "project,text,ending,expected_range",
    [
        (
            "sphinx-default",
            ":ref:`some_text",
            "`",
            Range(
                start=Position(line=0, character=6), end=Position(line=0, character=15)
            ),
        ),
        (
            "sphinx-default",
            "find out more :ref:`some_text",
            "`",
            Range(
                start=Position(line=0, character=20), end=Position(line=0, character=29)
            ),
        ),
        (
            "sphinx-default",
            ":ref:`more info <some_text",
            ">`",
            Range(
                start=Position(line=0, character=17), end=Position(line=0, character=26)
            ),
        ),
        (
            "sphinx-default",
            ":download:`_static/vscode_screenshot.png",
            "`",
            Range(
                start=Position(line=0, character=19), end=Position(line=0, character=40)
            ),
        ),
        (
            "sphinx-default",
            ":download:`this link <_static/vscode_screenshot.png",
            ">`",
            Range(
                start=Position(line=0, character=30), end=Position(line=0, character=51)
            ),
        ),
    ],
)
async def test_role_target_insert_range(
    client_server, project, text, ending, expected_range
):
    """Ensure that we generate completion items that work well with existing text."""

    test = await client_server(project)  # type: ClientServer
    test_uri = test.server.workspace.root_uri + "/test.rst"

    results = await completion_request(test, test_uri, text)
    assert len(results.items) > 0

    for item in results.items:
        assert item.text_edit.new_text.endswith(ending)
        assert item.text_edit.range == expected_range


@py.test.mark.parametrize(
    "string, expected",
    [
        ("::", None),
        (":", {"role": ":"}),
        (":ref", {"name": "ref", "role": ":ref"}),
        (":code-block", {"name": "code-block", "role": ":code-block"}),
        (":c:func:", {"name": "func", "domain": "c", "role": ":c:func:"}),
        (":cpp:func:", {"name": "func", "domain": "cpp", "role": ":cpp:func:"}),
        (":ref:`", {"name": "ref", "role": ":ref:", "target": "`"}),
        (
            ":code-block:`",
            {"name": "code-block", "role": ":code-block:", "target": "`"},
        ),
        (
            ":c:func:`",
            {"name": "func", "domain": "c", "role": ":c:func:", "target": "`"},
        ),
        (
            ":ref:`some_label",
            {
                "name": "ref",
                "role": ":ref:",
                "label": "some_label",
                "target": "`some_label",
            },
        ),
        (
            ":code-block:`some_label",
            {
                "name": "code-block",
                "role": ":code-block:",
                "label": "some_label",
                "target": "`some_label",
            },
        ),
        (
            ":c:func:`some_label",
            {
                "name": "func",
                "domain": "c",
                "role": ":c:func:",
                "label": "some_label",
                "target": "`some_label",
            },
        ),
        (
            ":ref:`some_label`",
            {
                "name": "ref",
                "role": ":ref:",
                "label": "some_label",
                "target": "`some_label`",
            },
        ),
        (
            ":code-block:`some_label`",
            {
                "name": "code-block",
                "role": ":code-block:",
                "label": "some_label",
                "target": "`some_label`",
            },
        ),
        (
            ":c:func:`some_label`",
            {
                "name": "func",
                "domain": "c",
                "role": ":c:func:",
                "label": "some_label",
                "target": "`some_label`",
            },
        ),
        (
            ":ref:`see more <",
            {
                "name": "ref",
                "role": ":ref:",
                "alias": "see more ",
                "target": "`see more <",
            },
        ),
        (
            ":code-block:`see more <",
            {
                "name": "code-block",
                "role": ":code-block:",
                "alias": "see more ",
                "target": "`see more <",
            },
        ),
        (
            ":c:func:`see more <",
            {
                "name": "func",
                "domain": "c",
                "role": ":c:func:",
                "alias": "see more ",
                "target": "`see more <",
            },
        ),
        (
            ":ref:`see more <some_label",
            {
                "name": "ref",
                "role": ":ref:",
                "alias": "see more ",
                "label": "some_label",
                "target": "`see more <some_label",
            },
        ),
        (
            ":code-block:`see more <some_label",
            {
                "name": "code-block",
                "role": ":code-block:",
                "alias": "see more ",
                "label": "some_label",
                "target": "`see more <some_label",
            },
        ),
        (
            ":c:func:`see more <some_label",
            {
                "name": "func",
                "domain": "c",
                "role": ":c:func:",
                "alias": "see more ",
                "label": "some_label",
                "target": "`see more <some_label",
            },
        ),
        (
            ":ref:`see more <some_label>",
            {
                "name": "ref",
                "role": ":ref:",
                "alias": "see more ",
                "label": "some_label",
                "target": "`see more <some_label>",
            },
        ),
        (
            ":code-block:`see more <some_label>",
            {
                "name": "code-block",
                "role": ":code-block:",
                "alias": "see more ",
                "label": "some_label",
                "target": "`see more <some_label>",
            },
        ),
        (
            ":c:func:`see more <some_label>",
            {
                "name": "func",
                "domain": "c",
                "role": ":c:func:",
                "alias": "see more ",
                "label": "some_label",
                "target": "`see more <some_label>",
            },
        ),
        (
            ":ref:`see more <some_label>`",
            {
                "name": "ref",
                "role": ":ref:",
                "alias": "see more ",
                "label": "some_label",
                "target": "`see more <some_label>`",
            },
        ),
        (
            ":code-block:`see more <some_label>`",
            {
                "name": "code-block",
                "role": ":code-block:",
                "alias": "see more ",
                "label": "some_label",
                "target": "`see more <some_label>`",
            },
        ),
        (
            ":c:func:`see more <some_label>`",
            {
                "name": "func",
                "domain": "c",
                "role": ":c:func:",
                "alias": "see more ",
                "label": "some_label",
                "target": "`see more <some_label>`",
            },
        ),
    ],
)
def test_role_regex(string, expected):
    """Ensure that the regular expression we use to detect and parse roles works as
    expected.

    As a general rule, it's better to write tests at the LSP protocol level as that
    decouples the test cases from the implementation. However, roles and the
    corresponding regular expression are complex enough to warrant a test case on its
    own.

    As with most test cases, this one is parameterized with the following arguments::

        (":ref:", {"name": "ref"}),
        (".. directive::", None)

    The first argument is the string to test the pattern against, the second a
    dictionary containing the groups we expect to see in the resulting match object.
    Groups that appear in the resulting match object but not in the expected result will
    **not** fail the test.

    To test situations where the pattern should **not** match the input, pass ``None``
    as the second argument.

    To test situaions where the pattern should match, but we don't expect to see any
    groups pass an empty dictionary as the second argument.
    """

    match = ROLE.match(string)

    if expected is None:
        assert match is None
    else:
        assert match is not None

        for name, value in expected.items():
            assert match.groupdict().get(name, None) == value
