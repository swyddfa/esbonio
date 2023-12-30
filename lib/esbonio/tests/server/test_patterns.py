import pytest

from esbonio.sphinx_agent.types import DEFAULT_ROLE
from esbonio.sphinx_agent.types import DIRECTIVE
from esbonio.sphinx_agent.types import DIRECTIVE_OPTION
from esbonio.sphinx_agent.types import ROLE


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


@pytest.mark.parametrize(
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
            ":ref:`!some_label",
            {
                "name": "ref",
                "role": ":ref:",
                "label": "some_label",
                "target": "`!some_label",
                "modifier": "!",
            },
        ),
        (
            ":ref:`~some_label",
            {
                "name": "ref",
                "role": ":ref:",
                "label": "some_label",
                "target": "`~some_label",
                "modifier": "~",
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
            ":ref:`see more <!some_label",
            {
                "name": "ref",
                "role": ":ref:",
                "alias": "see more ",
                "label": "some_label",
                "target": "`see more <!some_label",
                "modifier": "!",
            },
        ),
        (
            ":code-block:`see more <~some_label",
            {
                "name": "code-block",
                "role": ":code-block:",
                "alias": "see more ",
                "label": "some_label",
                "target": "`see more <~some_label",
                "modifier": "~",
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

    To test situations where the pattern should match, but we don't expect to see any
    groups pass an empty dictionary as the second argument.
    """

    match = ROLE.search(string)

    if expected is None:
        assert match is None
    else:
        assert match is not None

        for name, value in expected.items():
            assert match.groupdict().get(name, None) == value


@pytest.mark.parametrize(
    "string, expected",
    [
        (
            "`",
            {"target": "`"},
        ),
        (
            ":ref:`",
            None,
        ),
        (
            ":ref:``",
            None,
        ),
        (
            ":py:func:`",
            None,
        ),
        (
            ":py:func:``",
            None,
        ),
        (
            "`!some_label",
            {
                "label": "some_label",
                "target": "`!some_label",
                "modifier": "!",
            },
        ),
        (
            "`~some_label",
            {
                "label": "some_label",
                "target": "`~some_label",
                "modifier": "~",
            },
        ),
        (
            "`some_label",
            {
                "label": "some_label",
                "target": "`some_label",
            },
        ),
        (
            "`some_label`",
            {
                "label": "some_label",
                "target": "`some_label`",
            },
        ),
        (
            "`see more <",
            {
                "alias": "see more ",
                "target": "`see more <",
            },
        ),
        (
            "`see more <!some_label",
            {
                "alias": "see more ",
                "label": "some_label",
                "target": "`see more <!some_label",
                "modifier": "!",
            },
        ),
        (
            "`see more <~some_label",
            {
                "alias": "see more ",
                "label": "some_label",
                "target": "`see more <~some_label",
                "modifier": "~",
            },
        ),
        (
            "`see more <some_label",
            {
                "alias": "see more ",
                "label": "some_label",
                "target": "`see more <some_label",
            },
        ),
        (
            "`see more <some_label>`",
            {
                "alias": "see more ",
                "label": "some_label",
                "target": "`see more <some_label>`",
            },
        ),
    ],
)
def test_default_role_regex(string, expected):
    """Ensure that the regular expression we use to detect and parse default roles works
    as expected.

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

    To test situations where the pattern should match, but we don't expect to see any
    groups pass an empty dictionary as the second argument.
    """

    match = DEFAULT_ROLE.search(string)

    if expected is None:
        assert match is None
    else:
        assert match is not None

        for name, value in expected.items():
            assert match.groupdict().get(name, None) == value
