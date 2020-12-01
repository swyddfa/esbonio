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

from esbonio.lsp import completions


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
    ],
)
def test_completion_suggestions(rst, doc, params, expected):
    """Ensure that the correct type of completions are suggested based on the location
    and type of completion asked for."""

    document = make_document(doc)
    rst.workspace.get_document = Mock(return_value=document)

    actual = completions(rst, params).items
    assert actual == expected
