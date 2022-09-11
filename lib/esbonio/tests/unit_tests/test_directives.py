import pytest

from esbonio.lsp.directives import DIRECTIVE
from esbonio.lsp.directives import DIRECTIVE_OPTION


@pytest.mark.parametrize(
    "string, expected",
    [
        (".", None),
        ("..", {"directive": ".."}),
        (".. d", {"directive": ".. d"}),
        (".. image::", {"name": "image", "directive": ".. image::"}),
        (".. c:", {"domain": "c", "directive": ".. c:"}),
        (".. |", {"directive": ".. |", "substitution": "|"}),
        (
            ".. |e",
            {"directive": ".. |e", "substitution": "|e", "substitution_text": "e"},
        ),
        (
            ".. |example",
            {
                "directive": ".. |example",
                "substitution": "|example",
                "substitution_text": "example",
            },
        ),
        (
            ".. |example|",
            {
                "directive": ".. |example|",
                "substitution": "|example|",
                "substitution_text": "example",
            },
        ),
        (
            ".. |example| replace::",
            {
                "directive": ".. |example| replace::",
                "substitution": "|example|",
                "substitution_text": "example",
                "name": "replace",
            },
        ),
        (
            ".. |example| replace:: some text here",
            {
                "directive": ".. |example| replace::",
                "substitution": "|example|",
                "substitution_text": "example",
                "name": "replace",
                "argument": "some text here",
            },
        ),
        (
            ".. c:function::",
            {"name": "function", "domain": "c", "directive": ".. c:function::"},
        ),
        (
            ".. image:: filename.png",
            {"name": "image", "argument": "filename.png", "directive": ".. image::"},
        ),
        (
            ".. image:: filename.png  ",
            {"name": "image", "argument": "filename.png", "directive": ".. image::"},
        ),
        (
            ".. image:: filename.png\r",
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
            assert match.groupdict().get(name, None) == value, name


@pytest.mark.parametrize(
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
