import logging
import sys
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import pytest
from pygls.lsp.types import CompletionItem
from pygls.lsp.types import Location
from pygls.lsp.types import Position
from pygls.lsp.types import Range

from esbonio.lsp import CompletionContext
from esbonio.lsp import DefinitionContext
from esbonio.lsp import DocumentLinkContext
from esbonio.lsp.roles import DEFAULT_ROLE
from esbonio.lsp.roles import ROLE
from esbonio.lsp.roles import RoleLanguageFeature
from esbonio.lsp.roles import Roles

if sys.version_info.minor < 8:
    from mock import Mock
else:
    from unittest.mock import Mock


logger = logging.getLogger(__name__)


class Simple(RoleLanguageFeature):
    """A simple role language feature for use in tests."""

    def __init__(self, names: List[str]):
        self.roles = {name: lambda x: x for name in names}

    def index_roles(self) -> Dict[str, Any]:
        """Return all known roles."""
        return self.roles

    def complete_targets(
        self, context: CompletionContext, name: str, domain: Optional[str]
    ) -> List[CompletionItem]:
        if name not in self.roles:
            return []

        return [CompletionItem(label=f"{r}-{name}") for r in self.roles]

    def find_target_definitions(
        self, context: DefinitionContext, name: str, domain: str, label: str
    ) -> List[Location]:

        if name not in self.roles:
            return []

        return [
            Location(
                uri=f"file:///{name}.rst",
                range=Range(
                    start=Position(line=1, character=0),
                    end=Position(line=2, character=0),
                ),
            )
        ]

    def resolve_target_link(
        self, context: DocumentLinkContext, name: str, domain: Optional[str], label: str
    ) -> Tuple[Optional[str], Optional[str]]:

        if name not in self.roles:
            return None, None

        return f"file:///{name}.rst", None

    # The default `suggest_roles` implementation should be sufficient.
    # The default `get_implementation` implementation should be sufficient.


class Broken(RoleLanguageFeature):
    """A role language feature that only throws exceptions."""

    def index_roles(self) -> Dict[str, Any]:
        """Return all known roles."""
        raise NotImplementedError()

    def complete_targets(
        self, context: CompletionContext, name: str, domain: Optional[str]
    ) -> List[CompletionItem]:
        raise NotImplementedError()

    def find_target_definitions(
        self, context: DefinitionContext, name: str, domain: str, label: str
    ) -> List[Location]:
        raise NotImplementedError()

    def resolve_target_link(
        self, context: DocumentLinkContext, name: str, domain: Optional[str], label: str
    ) -> Tuple[Optional[str], Optional[str]]:
        raise NotImplementedError()

    # The default `suggest_roles` implementation should be sufficient.
    # The default `get_implementation` implementation should be sufficient.


@pytest.fixture()
def simple():
    """A simple functional instance of the roles language feature"""

    f1 = Simple(["one", "two"])
    f2 = Simple(["three", "four"])

    roles = Roles(Mock())
    roles.add_feature(f1)
    roles.add_feature(f2)

    return roles


@pytest.fixture()
def broken():
    """An instance of the roles language feature with sub features that will throw
    errors."""

    f1 = Simple(["one", "two"])
    f2 = Broken()
    f3 = Simple(["three", "four"])

    roles = Roles(Mock())
    roles.add_feature(f1)
    roles.add_feature(f2)
    roles.add_feature(f3)

    return roles


def test_get_roles(simple: Roles):
    """Ensure that we can correctly combine roles from multiple sources."""

    items = simple.get_roles()
    assert list(items.keys()) == ["one", "two", "three", "four"]

    # All should be well
    simple.logger.error.assert_not_called()


def test_get_roles_error(broken: Roles):
    """Ensure that we can gracefully handle errors in role langauge features."""

    items = broken.get_roles()
    assert list(items.keys()) == ["one", "two", "three", "four"]

    # The error should have been logged.
    broken.logger.error.assert_called_once()
    args = broken.logger.error.call_args.args
    assert args[0].startswith("Unable to index roles")


def test_get_implementation(simple: Roles):
    """Ensure that we can correctly look up roles from multiple sources."""

    impl = simple.get_implementation("one", None)
    assert callable(impl)

    impl = simple.get_implementation("four", None)
    assert callable(impl)

    # All should be well
    simple.logger.error.assert_not_called()


def test_get_implementation_error(broken: Roles):
    """Ensure that we can gracefully handle errors in role language features."""

    impl = broken.get_implementation("four", None)
    assert callable(impl)

    # The error should've been logged
    broken.logger.error.assert_called_once()
    args = broken.logger.error.call_args.args
    assert args[0].startswith("Unable to get implementation for")


def test_suggest_roles(simple: Roles):
    """Ensure that we can correctly combine roles from multiple sources."""

    context = CompletionContext(
        doc=Mock(), location="rst", match=Mock(), position=Mock(), capabilities=Mock()
    )

    items = simple.suggest_roles(context)
    assert [i[0] for i in items] == ["one", "two", "three", "four"]
    assert all([callable(i[1]) for i in items])

    # All should be well
    simple.logger.error.assert_not_called()


def test_suggest_roles_error(broken: Roles):
    """Ensure that we can gracefully handle errors in role language features."""

    context = CompletionContext(
        doc=Mock(), location="rst", match=Mock(), position=Mock(), capabilities=Mock()
    )

    items = broken.suggest_roles(context)
    assert [i[0] for i in items] == ["one", "two", "three", "four"]
    assert all([callable(i[1]) for i in items])

    # The error should've been logged
    broken.logger.error.assert_called_once()
    args = broken.logger.error.call_args.args
    assert args[0].startswith("Unable to suggest roles")


def test_find_target_definitions(simple: Roles):
    """Ensure that we can find target definitions using multiple sources."""

    context = DefinitionContext(
        doc=Mock(), location="rst", match=Mock(), position=Mock()
    )

    locations = simple.find_target_definitions(context, "one", "", "example")
    assert locations[0].uri == "file:///one.rst"

    locations = simple.find_target_definitions(context, "four", "", "example")
    assert locations[0].uri == "file:///four.rst"

    # All should be well
    simple.logger.error.assert_not_called()


def test_find_target_definitions_error(broken: Roles):
    """Ensure that we can gracefully handle errors in role language features."""

    context = DefinitionContext(
        doc=Mock(), location="rst", match=Mock(), position=Mock()
    )

    locations = broken.find_target_definitions(context, "four", "", "example")
    assert locations[0].uri == "file:///four.rst"

    # The error should've been logged
    broken.logger.error.assert_called_once()
    args = broken.logger.error.call_args.args
    assert args[0].startswith("Unable to find definitions")


def test_resolve_target_link(simple: Roles):
    """Ensure that we can resolve links using multiple sources."""

    context = DocumentLinkContext(doc=Mock(), capabilities=Mock())

    target, _ = simple.resolve_target_link(context, "one", "", "example")
    assert target == "file:///one.rst"

    target, _ = simple.resolve_target_link(context, "four", "", "example")
    assert target == "file:///four.rst"

    # All should be well
    simple.logger.error.assert_not_called()


def test_resolve_target_link_error(broken: Roles):
    """Ensure that we can gracefully handle errors in role language features."""

    context = DocumentLinkContext(doc=Mock(), capabilities=Mock())

    target, _ = broken.resolve_target_link(context, "four", "", "example")
    assert target == "file:///four.rst"

    # The error should've been logged
    broken.logger.error.assert_called_once()
    args = broken.logger.error.call_args.args
    assert args[0].startswith("Unable to resolve target link")


def test_suggest_targets(simple: Roles):
    """Ensure that we can collect target completions from multiple sources."""

    context = CompletionContext(
        doc=Mock(), location="rst", match=Mock(), position=Mock(), capabilities=Mock()
    )

    items = simple.suggest_targets(context, "one", "")
    assert [i.label for i in items] == ["one-one", "two-one"]

    items = simple.suggest_targets(context, "four", "")
    assert [i.label for i in items] == ["three-four", "four-four"]

    # All should be well
    simple.logger.error.assert_not_called()


def test_suggest_targets_error(broken: Roles):
    """Ensure that we can gracefully handle errors in role language features."""

    context = CompletionContext(
        doc=Mock(), location="rst", match=Mock(), position=Mock(), capabilities=Mock()
    )

    items = broken.suggest_targets(context, "four", "")
    assert [i.label for i in items] == ["three-four", "four-four"]

    # The error should've been logged
    broken.logger.error.assert_called_once()
    args = broken.logger.error.call_args.args
    assert args[0].startswith("Unable to suggest targets for")


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
