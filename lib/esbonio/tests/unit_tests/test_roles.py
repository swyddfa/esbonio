import pytest

from esbonio.lsp.roles import DEFAULT_ROLE
from esbonio.lsp.roles import ROLE


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
