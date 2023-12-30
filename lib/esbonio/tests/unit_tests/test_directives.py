import sys
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Tuple

import pytest
from docutils.parsers.rst import Directive
from lsprotocol.types import Location
from lsprotocol.types import Position
from lsprotocol.types import Range

from esbonio.lsp import CompletionContext
from esbonio.lsp import DefinitionContext
from esbonio.lsp.directives import DirectiveLanguageFeature
from esbonio.lsp.directives import Directives
from esbonio.lsp.rst import DocumentLinkContext
from esbonio.lsp.rst.config import ServerCompletionConfig

if sys.version_info.minor < 8:
    from mock import Mock
else:
    from unittest.mock import Mock


class Simple(DirectiveLanguageFeature):
    """A simple directive language feature for use in tests."""

    def __init__(self, names: List[str]):
        self.directives = {name: Directive for name in names}

    def index_directives(self) -> Dict[str, Directive]:
        return self.directives

    def suggest_options(
        self, context: CompletionContext, directive: str, domain: Optional[str]
    ) -> Iterable[str]:
        return iter(directive) if directive in self.directives else []

    # The default `suggest_directives` implementation should be sufficient.
    # The default `get_implementation` implementation should be sufficient.

    def find_argument_definitions(
        self,
        context: DefinitionContext,
        directive: str,
        domain: Optional[str],
        argument: str,
    ) -> List[Location]:
        if directive not in self.directives:
            return []

        return [
            Location(
                uri=f"file:///{directive}.rst",
                range=Range(
                    start=Position(line=1, character=0),
                    end=Position(line=2, character=0),
                ),
            )
        ]

    def resolve_argument_link(
        self,
        context: DocumentLinkContext,
        directive: str,
        domain: Optional[str],
        argument: str,
    ) -> Tuple[Optional[str], Optional[str]]:
        if directive not in self.directives:
            return None, None

        return f"file:///{directive}.rst", None


class Broken(DirectiveLanguageFeature):
    """A directive language feature that only throws exceptions."""

    def index_directives(self) -> Dict[str, Directive]:
        raise NotImplementedError()

    def suggest_options(
        self, context: CompletionContext, directive: str, domain: Optional[str]
    ) -> Iterable[str]:
        raise NotImplementedError()

    # The default `suggest_directives` implementation should be sufficient.
    # The default `get_implementation` implementation should be sufficient.

    def find_argument_definitions(
        self,
        context: DefinitionContext,
        directive: str,
        domain: Optional[str],
        argument: str,
    ) -> List[Location]:
        raise NotImplementedError()

    def resolve_argument_link(
        self,
        context: DocumentLinkContext,
        directive: str,
        domain: Optional[str],
        argument: str,
    ) -> Tuple[Optional[str], Optional[str]]:
        raise NotImplementedError()


@pytest.fixture()
def simple():
    """A simple functional instance of the directive language feature"""

    f1 = Simple(["one", "two"])
    f2 = Simple(["three", "four"])

    directives = Directives(Mock())
    directives.add_feature(f1)
    directives.add_feature(f2)

    return directives


@pytest.fixture()
def broken():
    """A an instance of the directive language feature with sub features that will
    throw errors."""

    f1 = Simple(["one", "two"])
    f2 = Broken()
    f3 = Simple(["three", "four"])

    directives = Directives(Mock())
    directives.add_feature(f1)
    directives.add_feature(f2)
    directives.add_feature(f3)

    return directives


def test_get_directives(simple: Directives):
    """Ensure that we can correctly combine directives from multiple sources."""

    items = simple.get_directives()
    assert list(items.keys()) == ["one", "two", "three", "four"]
    assert all([cls == Directive for cls in items.values()])

    # All should be well
    simple.logger.error.assert_not_called()


def test_get_directives_error(broken: Directives):
    """Ensure we can gracefully handle errors in directive language features."""

    items = broken.get_directives()
    assert list(items.keys()) == ["one", "two", "three", "four"]
    assert all([cls == Directive for cls in items.values()])

    # The error should've been logged
    broken.logger.error.assert_called_once()
    args = broken.logger.error.call_args.args
    assert args[0].startswith("Unable to index directives")


def test_get_implementation(simple: Directives):
    """Ensure that we can correctly look up directives from multiple sources."""

    impl = simple.get_implementation("one", None)
    assert impl == Directive

    impl = simple.get_implementation("four", None)
    assert impl == Directive

    # All should be well
    simple.logger.error.assert_not_called()


def test_get_implementation_error(broken: Directives):
    """Ensure we can gracefully handle errors in directive language features."""

    impl = broken.get_implementation("four", None)
    assert impl == Directive

    # The error should've been logged
    broken.logger.error.assert_called_once()
    args = broken.logger.error.call_args.args
    assert args[0].startswith("Unable to get implementation for")


def test_suggest_directives(simple: Directives):
    """Ensure that we can correctly combine directives from multiple sources."""

    context = CompletionContext(
        doc=Mock(),
        location="rst",
        match=Mock(),
        position=Mock(),
        config=ServerCompletionConfig(),
        capabilities=Mock(),
    )
    items = simple.suggest_directives(context)

    assert [i[0] for i in items] == ["one", "two", "three", "four"]
    assert all([i[1] == Directive for i in items])

    # All should be well
    simple.logger.error.assert_not_called()


def test_suggest_directives_error(broken: Directives):
    """Ensure that we can gracefully handle errors in directive language features."""

    context = CompletionContext(
        doc=Mock(),
        location="rst",
        match=Mock(),
        position=Mock(),
        config=ServerCompletionConfig(),
        capabilities=Mock(),
    )
    items = broken.suggest_directives(context)

    assert [i[0] for i in items] == ["one", "two", "three", "four"]
    assert all([i[1] == Directive for i in items])

    # The error should've been logged
    broken.logger.error.assert_called_once()
    args = broken.logger.error.call_args.args
    assert args[0].startswith("Unable to suggest directives")


def test_suggest_options(simple: Directives):
    """Ensure that we can correctly combine directives from multiple sources."""

    context = CompletionContext(
        doc=Mock(),
        location="rst",
        match=Mock(),
        position=Mock(),
        config=ServerCompletionConfig(),
        capabilities=Mock(),
    )

    items = simple.suggest_options(context, "four", None)
    assert list(items) == ["f", "o", "u", "r"]

    # All should be well
    simple.logger.error.assert_not_called()


def test_suggest_options_error(broken: Directives):
    """Ensure that we can gracefully handle errors in directive language features."""

    context = CompletionContext(
        doc=Mock(),
        location="rst",
        match=Mock(),
        position=Mock(),
        config=ServerCompletionConfig(),
        capabilities=Mock(),
    )

    items = broken.suggest_options(context, "four", None)
    assert list(items) == ["f", "o", "u", "r"]

    # The error should've been logged
    broken.logger.error.assert_called_once()
    args = broken.logger.error.call_args.args
    assert args[0].startswith("Unable to suggest options for ")


def test_find_argument_definitions(simple: Directives):
    """Ensure that we can correctly combine definitions from multiple sources."""

    context = DefinitionContext(
        doc=Mock(), location="rst", match=Mock(), position=Mock()
    )

    locations = simple.find_argument_definition(context, "one", "", "example")
    assert locations[0].uri == "file:///one.rst"

    locations = simple.find_argument_definition(context, "four", "", "example")
    assert locations[0].uri == "file:///four.rst"

    # All should be well
    simple.logger.error.assert_not_called()


def test_find_argument_definitions_error(broken: Directives):
    """Ensure that we can gracefully handle errors in directive language features."""

    context = DefinitionContext(
        doc=Mock(), location="rst", match=Mock(), position=Mock()
    )

    locations = broken.find_argument_definition(context, "four", "", "example")
    assert locations[0].uri == "file:///four.rst"

    # The error should've been logged
    broken.logger.error.assert_called_once()
    args = broken.logger.error.call_args.args
    assert args[0].startswith("Unable to find definitions")


def test_resolve_argument_link(simple: Directives):
    """Ensure that we can use multiple sources to resolve a document link."""

    context = DocumentLinkContext(doc=Mock(), capabilities=Mock())

    target, _ = simple.resolve_argument_link(context, "one", "", "example")
    assert target == "file:///one.rst"

    target, _ = simple.resolve_argument_link(context, "four", "", "example")
    assert target == "file:///four.rst"

    # All should be well
    simple.logger.error.assert_not_called()


def test_resolve_argument_link_error(broken: Directives):
    """Ensure that we gracefully handle errors when resolving argument links."""

    context = DocumentLinkContext(doc=Mock(), capabilities=Mock())

    target, _ = broken.resolve_argument_link(context, "four", "", "example")
    assert target == "file:///four.rst"

    # The error should've been logged
    broken.logger.error.assert_called_once()
    args = broken.logger.error.call_args.args
    assert args[0].startswith("Unable to resolve argument link")
