"""Testing the logic behind suggesting completions.

This assumes that the objects we can complete, directives, roles, references etc have
already been discovered. So these tests focus on "given a completion request at this
position, what should the suggestions be?"

These tests rely heavily on mocking, it might be better to replace them with more
integration style tests once the end-to-end picture is better understood.
"""
from typing import Optional
import logging
import py.test

from mock import Mock
from pygls.types import (
    CompletionItem,
    CompletionContext,
    CompletionItemKind,
    CompletionTriggerKind,
    CompletionParams,
    Position,
    TextDocumentIdentifier,
)
from pygls.workspace import Document, Workspace

from esbonio.lsp.completion import completions
from esbonio.lsp.initialize import discover_roles, discover_targets


def make_document(contents) -> Document:
    """Helper that constructs a document that can be placed in a workspace."""

    uri = "file://fake_doc.rst"
    return Document(uri, contents)


def make_params(
    line: int = 0, character: int = 0, trigger: Optional[str] = None
) -> CompletionParams:
    """Helper that makes it easier to construct the completion params."""

    trigger_kind = CompletionTriggerKind.Invoked

    if trigger is not None:
        trigger_kind = CompletionTriggerKind.TriggerCharacter

    return CompletionParams(
        text_document=TextDocumentIdentifier(uri="file://fake_doc.rst"),
        position=Position(line=line, character=character),
        context=CompletionContext(trigger_kind=trigger_kind, trigger_character=trigger),
    )


EXAMPLE_DIRECTIVES = [CompletionItem("doctest", kind=CompletionItemKind.Class)]
EXAMPLE_ROLES = [CompletionItem("ref", kind=CompletionItemKind.Function)]

EXAMPLE_DOCS = [CompletionItem("reference/index", kind=CompletionItemKind.Reference)]
EXAMPLE_REFS = [CompletionItem("search", kind=CompletionItemKind.Reference)]


@py.test.fixture()
def rst():
    """A mock rst language server instance.

    Originally based on:
    https://github.com/openlawlibrary/pygls/blob/aee66189e8233c34dba4c13a9a87e6708fb03810/examples/json-extension/server/tests/unit/test_features.py
    """

    class LanguageServer:
        def __init__(self):
            self.workspace = Workspace("", None)

    server = LanguageServer()
    server.publish_diagnostics = Mock()
    server.show_message = Mock()
    server.show_message_log = Mock()

    server.logger = logging.getLogger(__name__)

    # Mock the data that is used to provide the completions.
    server.directives = {c.label: c for c in EXAMPLE_DIRECTIVES}
    server.roles = {c.label: c for c in EXAMPLE_ROLES}

    server.target_types = {"ref": "label", "doc": "doc"}
    server.targets = {"label": EXAMPLE_REFS, "doc": EXAMPLE_DOCS}

    return server


@py.test.mark.parametrize(
    "doc,params,expected",
    [
        # Directive Suggestions.
        (".", make_params(character=1, trigger="."), []),
        ("..", make_params(character=2, trigger="."), EXAMPLE_DIRECTIVES),
        (".. ", make_params(character=3), EXAMPLE_DIRECTIVES),
        (".. d", make_params(character=4), EXAMPLE_DIRECTIVES),
        (".. code-b", make_params(character=9), EXAMPLE_DIRECTIVES),
        (".. doctest:: ", make_params(character=13), []),
        (".. code-block:: ", make_params(character=16), []),
        ("   .", make_params(character=4, trigger="."), []),
        ("   ..", make_params(character=5, trigger="."), EXAMPLE_DIRECTIVES),
        ("   .. ", make_params(character=6), EXAMPLE_DIRECTIVES),
        ("   .. d", make_params(character=7), EXAMPLE_DIRECTIVES),
        ("   .. code-b", make_params(character=12), EXAMPLE_DIRECTIVES),
        ("   .. doctest:: ", make_params(character=16), []),
        ("   .. code-block:: ", make_params(character=19), []),
        # Role Suggestions
        (":", make_params(character=1, trigger=":"), EXAMPLE_ROLES),
        (":r", make_params(character=2), EXAMPLE_ROLES),
        ("   :", make_params(character=4), EXAMPLE_ROLES),
        ("   :r", make_params(character=5), EXAMPLE_ROLES),
        ("some text :", make_params(character=11), EXAMPLE_ROLES),
        ("   some text :", make_params(character=14), EXAMPLE_ROLES),
        (".. _some_target:", make_params(character=16), []),
        ("   .. _some_target:", make_params(character=19), []),
        (":ref:", make_params(character=5), []),
        # Role Target Suggestions
        (":ref:`", make_params(character=6), EXAMPLE_REFS),
        (":ref:``", make_params(character=6), EXAMPLE_REFS),
        ("   :ref:`", make_params(character=9), EXAMPLE_REFS),
        ("   :ref:``", make_params(character=9), EXAMPLE_REFS),
        (":doc:`", make_params(character=6), EXAMPLE_DOCS),
        (":doc:``", make_params(character=6), EXAMPLE_DOCS),
        ("   :doc:`", make_params(character=9), EXAMPLE_DOCS),
        ("   :doc:``", make_params(character=9), EXAMPLE_DOCS),
    ],
)
def test_completion_suggestions(rst, doc, params, expected):
    """Ensure that the correct type of completions are suggested based on the location
    and type of completion asked for."""

    document = make_document(doc)
    rst.workspace.get_document = Mock(return_value=document)

    actual = completions(rst, params).items
    assert actual == expected


@py.test.mark.parametrize(
    "project,expected,unexpected",
    [
        (
            "sphinx-default",
            [
                "emphasis",
                "subscript",
                "raw",
                "func",
                "meth",
                "class",
                "ref",
                "doc",
                "term",
            ],
            ["named-reference", "restructuredtext-unimplemented-role"],
        )
    ],
)
def test_role_discovery(sphinx, project, expected, unexpected):
    """Ensure that we can discover the roles from the various places they are stored."""

    app = sphinx(project)
    roles = discover_roles(app)

    for name in expected:
        assert name in roles.keys(), "Missing expected role '{}'".format(name)

    for name in unexpected:
        assert name not in roles.keys(), "Unexpected role '{}'".format(name)


@py.test.mark.parametrize(
    "project,type,kind,expected",
    [
        (
            "sphinx-default",
            "attribute",
            CompletionItemKind.Field,
            {"pythagoras.Triangle.a", "pythagoras.Triangle.b", "pythagoras.Triangle.c"},
        ),
        ("sphinx-default", "class", CompletionItemKind.Class, {"pythagoras.Triangle"}),
        (
            "sphinx-default",
            "doc",
            CompletionItemKind.File,
            {"glossary", "index", "theorems/index", "theorems/pythagoras"},
        ),
        (
            "sphinx-default",
            "envvar",
            CompletionItemKind.Variable,
            {"ANGLE_UNIT", "PRECISION"},
        ),
        (
            "sphinx-default",
            "function",
            CompletionItemKind.Function,
            {"pythagoras.calc_side", "pythagoras.calc_hypotenuse"},
        ),
        (
            "sphinx-default",
            "method",
            CompletionItemKind.Method,
            {"pythagoras.Triangle.is_right_angled"},
        ),
        ("sphinx-default", "module", CompletionItemKind.Module, {"pythagoras"}),
        (
            "sphinx-default",
            "label",
            CompletionItemKind.Reference,
            {
                "genindex",
                "modindex",
                "py-modindex",
                "pythagoras_theorem",
                "search",
                "welcome",
            },
        ),
        (
            "sphinx-default",
            "term",
            CompletionItemKind.Text,
            {"hypotenuse", "right angle"},
        ),
    ],
)
def test_target_discovery(sphinx, project, type, kind, expected):
    """Ensure that we can discover the appropriate targets to complete on."""

    app = sphinx(project)
    app.builder.read()
    targets = discover_targets(app)

    assert type in targets
    assert expected == {item.label for item in targets[type]}
    assert kind == targets[type][0].kind
