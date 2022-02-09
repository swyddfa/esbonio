import itertools

import py.test
from pygls.lsp.types import Position
from pygls.lsp.types import Range

from esbonio.lsp.directives import DIRECTIVE
from esbonio.lsp.directives import DIRECTIVE_OPTION
from esbonio.lsp.testing import ClientServer
from esbonio.lsp.testing import completion_request
from esbonio.lsp.testing import sphinx_version

DEFAULT_EXPECTED = {
    "function",
    "module",
    "option",
    "program",
    "image",
    "toctree",
    "c:macro",
    "c:function",
}

DEFAULT_UNEXPECTED = {
    "autoclass",
    "automodule",
    "py:function",
    "py:module",
    "std:program",
    "std:option",
    "restructuredtext-test-directive",
}

EXTENSIONS_EXPECTED = {
    "autoclass",
    "automodule",
    "py:function",
    "py:module",
    "option",
    "program",
    "image",
    "toctree",
    "macro",
    "function",
}

EXTENSIONS_UNEXPECTED = {
    "c:macro",
    "module",
    "std:program",
    "std:option",
    "restructuredtext-test-directive",
}


@py.test.mark.asyncio
@py.test.mark.parametrize(
    "project,text,expected,unexpected",
    [
        ("sphinx-default", ".", None, None),
        ("sphinx-default", "..", DEFAULT_EXPECTED, DEFAULT_UNEXPECTED),
        ("sphinx-default", ".. ", DEFAULT_EXPECTED, DEFAULT_UNEXPECTED),
        ("sphinx-default", ".. d", DEFAULT_EXPECTED, DEFAULT_UNEXPECTED),
        ("sphinx-default", ".. code-b", DEFAULT_EXPECTED, DEFAULT_UNEXPECTED),
        ("sphinx-default", ".. codex-block:: ", None, None),
        ("sphinx-default", ".. py:", None, None),
        (
            "sphinx-default",
            ".. c:",
            {"c:macro", "c:function"},
            {"function", "image", "toctree"},
        ),
        ("sphinx-default", ".. _some_label:", None, None),
        ("sphinx-default", "   .", None, None),
        ("sphinx-default", "   ..", DEFAULT_EXPECTED, DEFAULT_UNEXPECTED),
        ("sphinx-default", "   .. ", DEFAULT_EXPECTED, DEFAULT_UNEXPECTED),
        ("sphinx-default", "   .. d", DEFAULT_EXPECTED, DEFAULT_UNEXPECTED),
        ("sphinx-default", "   .. doctest:: ", None, None),
        ("sphinx-default", "   .. code-b", DEFAULT_EXPECTED, DEFAULT_UNEXPECTED),
        ("sphinx-default", "   .. codex-block:: ", None, None),
        ("sphinx-default", "   .. py:", None, None),
        ("sphinx-default", "   .. _some_label:", None, None),
        (
            "sphinx-default",
            "   .. c:",
            {"c:macro", "c:function"},
            {"function", "image", "toctree"},
        ),
        ("sphinx-extensions", ".", None, None),
        ("sphinx-extensions", "..", EXTENSIONS_EXPECTED, EXTENSIONS_UNEXPECTED),
        ("sphinx-extensions", ".. ", EXTENSIONS_EXPECTED, EXTENSIONS_UNEXPECTED),
        ("sphinx-extensions", ".. d", EXTENSIONS_EXPECTED, EXTENSIONS_UNEXPECTED),
        ("sphinx-extensions", ".. code-b", EXTENSIONS_EXPECTED, EXTENSIONS_UNEXPECTED),
        ("sphinx-extensions", ".. codex-block:: ", None, None),
        ("sphinx-extensions", ".. _some_label:", None, None),
        (
            "sphinx-extensions",
            ".. py:",
            {"py:function", "py:module"},
            {"image, toctree", "macro", "function"},
        ),
        ("sphinx-extensions", ".. c:", None, None),
        ("sphinx-extensions", "   .", None, None),
        ("sphinx-extensions", "   ..", EXTENSIONS_EXPECTED, EXTENSIONS_UNEXPECTED),
        ("sphinx-extensions", "   .. ", EXTENSIONS_EXPECTED, EXTENSIONS_UNEXPECTED),
        ("sphinx-extensions", "   .. d", EXTENSIONS_EXPECTED, EXTENSIONS_UNEXPECTED),
        ("sphinx-extensions", "   .. doctest:: ", None, None),
        ("sphinx-extensions", "   .. _some_label:", None, None),
        (
            "sphinx-extensions",
            "   .. code-b",
            EXTENSIONS_EXPECTED,
            EXTENSIONS_UNEXPECTED,
        ),
        ("sphinx-extensions", "   .. codex-block:: ", None, None),
        (
            "sphinx-extensions",
            ".. py:",
            {"py:function", "py:module"},
            {"image, toctree", "macro", "function"},
        ),
        ("sphinx-extensions", "   .. c:", None, None),
    ],
)
async def test_directive_completions(
    client_server, project, text, expected, unexpected
):

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


@py.test.mark.asyncio
@py.test.mark.parametrize(
    "project,text,expected,unexpected",
    [
        ("sphinx-default", ".. image:: f.png\n\f   :", IMAGE_OPTS, {"ref", "func"}),
        (
            "sphinx-default",
            ".. image:: f.png\n   :align:\n\f   :",
            IMAGE_OPTS,
            {"ref", "func"},
        ),
        ("sphinx-default", ".. function:: foo\n\f   :", PY_FUNC_OPTS, {"ref", "func"}),
        (
            "sphinx-default",
            ".. autoclass:: x.y.A\n\f   :",
            set(),
            {"ref", "func"} | AUTOCLASS_OPTS,
        ),
        (
            "sphinx-default",
            "   .. image:: f.png\n\f      :",
            IMAGE_OPTS,
            {"ref", "func"},
        ),
        (
            "sphinx-default",
            "   .. function:: foo\n\f      :",
            PY_FUNC_OPTS,
            {"ref", "func"},
        ),
        (
            "sphinx-default",
            "   .. c:function:: foo\n\f      :",
            C_FUNC_OPTS,
            {"ref", "func"},
        ),
        (
            "sphinx-default",
            "   .. autoclass:: x.y.A\n\f      :",
            set(),
            {"ref", "func"} | AUTOCLASS_OPTS,
        ),
        ("sphinx-extensions", ".. image:: f.png\n\f   :", IMAGE_OPTS, {"ref", "func"}),
        (
            "sphinx-extensions",
            ".. function:: foo\n\f   :",
            C_FUNC_OPTS,
            {"ref", "func"},
        ),
        (
            "sphinx-extensions",
            ".. py:function:: foo\n\f   :",
            PY_FUNC_OPTS,
            {"ref", "func"},
        ),
        (
            "sphinx-extensions",
            ".. autoclass:: x.y.A\n\f   :",
            AUTOCLASS_OPTS,
            {"ref", "func"},
        ),
        (
            "sphinx-extensions",
            "   .. image:: f.png\n\f      :",
            IMAGE_OPTS,
            {"ref", "func"},
        ),
        (
            "sphinx-extensions",
            "   .. function:: foo\n\f      :",
            C_FUNC_OPTS,
            {"ref", "func"},
        ),
        (
            "sphinx-extensions",
            "   .. autoclass:: x.y.A\n\f      :",
            AUTOCLASS_OPTS,
            {"ref", "func"},
        ),
    ],
)
async def test_directive_option_completions(
    client_server, project, text, expected, unexpected
):

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
async def test_completion_suppression(client_server, extension, setup):
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

    test = await client_server("sphinx-default")
    test_uri = test.server.workspace.root_uri + f"/test.{extension}"

    text, expected, character = setup

    results = await completion_request(test, test_uri, text, character=character)
    assert (len(results.items) > 0) == expected


@py.test.mark.asyncio
@py.test.mark.parametrize(
    "project,text,character,expected_range",
    [
        (
            "sphinx-default",
            "..",
            None,
            Range(
                start=Position(line=0, character=0), end=Position(line=0, character=2)
            ),
        ),
        (
            "sphinx-default",
            ".. function",
            None,
            Range(
                start=Position(line=0, character=0), end=Position(line=0, character=11)
            ),
        ),
        (
            "sphinx-default",
            ".. function::",
            3,
            Range(
                start=Position(line=0, character=0), end=Position(line=0, character=13)
            ),
        ),
        (
            "sphinx-default",
            ".. function::\n\f   :",
            4,
            Range(
                start=Position(line=1, character=3), end=Position(line=1, character=4)
            ),
        ),
        (
            "sphinx-default",
            ".. function::\n\f   :align",
            4,
            Range(
                start=Position(line=1, character=3), end=Position(line=1, character=9)
            ),
        ),
        (
            "sphinx-default",
            ".. function::\n\f   :align: center",
            4,
            Range(
                start=Position(line=1, character=3), end=Position(line=1, character=10)
            ),
        ),
    ],
)
async def test_insert_range(client_server, project, text, character, expected_range):
    """Ensure that we generate completion items that work well with existing text.

    This test case is focused on the range of text a ``CompletionItem`` will modify
    if selected. This is to ensure that we don't create more work for the end user by
    corrupting the line we edit or leaving additional characters that are not required.

    Cases are parameterized and the inputs are expected to have the following format::

       ("sphinx-default", ".. image", 3, Range(...))

    where:

    - ``"sphinx-default"`` corresponds to the Sphinx project to execute the test case
      within.
    - ``".. image"`` corresponds to the text to insert into the test file
    - ``7`` is the character index to trigger the completion request at. If ``None`` it
      will default to the end of the line
    - ``Range(...)`` is the expected range the resulting ``CompletionItem`` should
      modify
    """

    test = await client_server(project)  # type: ClientServer
    test_uri = test.server.workspace.root_uri + "/test.rst"

    results = await completion_request(test, test_uri, text, character=character)
    assert len(results.items) > 0

    for item in results.items:
        assert item.text_edit.range == expected_range


@py.test.mark.parametrize(
    "string, expected",
    [
        (".", None),
        ("..", {"directive": ".."}),
        (".. d", {"directive": ".. d"}),
        (".. image::", {"name": "image", "directive": ".. image::"}),
        (".. c:", {"domain": "c", "directive": ".. c:"}),
        (
            ".. c:function::",
            {"name": "function", "domain": "c", "directive": ".. c:function::"},
        ),
        (
            ".. image:: filename.png",
            {"name": "image", "argument": "filename.png", "directive": ".. image::"},
        ),
        (
            ".. cpp:function:: malloc",
            {
                "name": "function",
                "domain": "cpp",
                "argument": "malloc",
                "directive": ".. cpp:function::",
            },
        ),
        (
            "   .. image:: filename.png",
            {"name": "image", "argument": "filename.png", "directive": ".. image::"},
        ),
        (
            "   .. cpp:function:: malloc",
            {
                "name": "function",
                "domain": "cpp",
                "argument": "malloc",
                "directive": ".. cpp:function::",
            },
        ),
        (
            ".. rst:directive:option::",
            {
                "name": "directive:option",
                "domain": "rst",
                "directive": ".. rst:directive:option::",
            },
        ),
        (
            "   .. rst:directive:option::",
            {
                "name": "directive:option",
                "domain": "rst",
                "directive": ".. rst:directive:option::",
            },
        ),
        (
            "   .. rst:directive:option:: height",
            {
                "name": "directive:option",
                "domain": "rst",
                "directive": ".. rst:directive:option::",
                "argument": "height",
            },
        ),
    ],
)
def test_directive_regex(string, expected):
    """Ensure that the regular expression we use to detect and parse directives
    works as expected.

    As with most test cases, this one is parameterized with the following arguments::

       (".. figure::", {"name": "figure"})

    The first argument is the string to test the pattern against, the second a
    dictionary containing the groups we expect to see in the resulting match object.
    Groups that appear in the resulting match object but not in the expected result
    will **not** fail the test.

    To test situations where the pattern should **not** match the input, pass ``None``
    as the second argument.

    To test situaions where the pattern should match, but we don't expect to see any
    groups pass an empty dictionary as the second argument.
    """

    match = DIRECTIVE.match(string)

    if expected is None:
        assert match is None
    else:
        assert match is not None

        for name, value in expected.items():
            assert match.groupdict().get(name, None) == value


@py.test.mark.parametrize(
    "string, expected",
    [
        (":", None),
        (":align", None),
        (":align:", None),
        (":align: center", None),
        ("   :", {"indent": "   ", "option": ":"}),
        ("   :align", {"indent": "   ", "option": ":align", "name": "align"}),
        ("   :align:", {"indent": "   ", "option": ":align:", "name": "align"}),
        (
            "   :align: center",
            {"indent": "   ", "option": ":align:", "name": "align", "value": "center"},
        ),
    ],
)
def test_directive_option_regex(string, expected):
    """Ensure that the regular expression we use to detect and parse directive
    options works as expected.

    As with most test cases, this one is parameterized with the following arguments::

       ("   :align:", {"name": "align"})

    The first argument is the string to test the pattern against, the second a
    dictionary containing the groups we expect to see in the resulting match object.
    Groups that appear in the resulting match object but not in the expected result
    will **not** fail the test.

    To test situations where the pattern should **not** match the input, pass ``None``
    as the second argument.

    To test situaions where the pattern should match, but we don't expect to see any
    groups pass an empty dictionary as the second argument.
    """

    match = DIRECTIVE_OPTION.match(string)

    if expected is None:
        assert match is None
    else:
        assert match is not None

        for name, value in expected.items():
            assert match.groupdict().get(name, None) == value
