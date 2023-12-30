import logging
import sys
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import pytest
from lsprotocol.types import CompletionItem
from lsprotocol.types import Location
from lsprotocol.types import Position
from lsprotocol.types import Range

from esbonio.lsp import CompletionContext
from esbonio.lsp import DefinitionContext
from esbonio.lsp import DocumentLinkContext
from esbonio.lsp.roles import RoleLanguageFeature
from esbonio.lsp.roles import Roles
from esbonio.lsp.rst.config import ServerCompletionConfig

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
        doc=Mock(),
        location="rst",
        match=Mock(),
        position=Mock(),
        config=ServerCompletionConfig(),
        capabilities=Mock(),
    )

    items = simple.suggest_roles(context)
    assert [i[0] for i in items] == ["one", "two", "three", "four"]
    assert all([callable(i[1]) for i in items])

    # All should be well
    simple.logger.error.assert_not_called()


def test_suggest_roles_error(broken: Roles):
    """Ensure that we can gracefully handle errors in role language features."""

    context = CompletionContext(
        doc=Mock(),
        location="rst",
        match=Mock(),
        position=Mock(),
        config=ServerCompletionConfig(),
        capabilities=Mock(),
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
        doc=Mock(),
        location="rst",
        match=Mock(),
        position=Mock(),
        config=ServerCompletionConfig(),
        capabilities=Mock(),
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
        doc=Mock(),
        location="rst",
        match=Mock(),
        position=Mock(),
        config=ServerCompletionConfig(),
        capabilities=Mock(),
    )

    items = broken.suggest_targets(context, "four", "")
    assert [i.label for i in items] == ["three-four", "four-four"]

    # The error should've been logged
    broken.logger.error.assert_called_once()
    args = broken.logger.error.call_args.args
    assert args[0].startswith("Unable to suggest targets for")
