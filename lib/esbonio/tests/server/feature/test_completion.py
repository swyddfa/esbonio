from __future__ import annotations

import re
import typing

import pytest
from lsprotocol import types
from pygls.workspace import TextDocument

from esbonio import server

if typing.TYPE_CHECKING:
    from typing import Optional
    from typing import Set


@pytest.mark.parametrize(
    "language, languages, expected",
    [
        ("rst", set(), True),
        ("markdown", set(), True),
        ("rst", {"markdown"}, False),
        ("rst", {"rst", "python"}, True),
    ],
)
def test_completion_trigger_languages(
    language: str, languages: Set[str], expected: bool
):
    """Ensure that ``CompletionTrigger`` responds to the given language correctly."""

    uri = server.Uri.parse("file:///test.txt")
    params = types.CompletionParams(
        position=types.Position(line=0, character=0),
        text_document=types.TextDocumentIdentifier(uri=str(uri)),
    )
    document = TextDocument(uri=str(uri), source="some text")

    trigger = server.CompletionTrigger(patterns=[re.compile(".*")], languages=languages)
    result = trigger(uri, params, document, language, types.ClientCapabilities())

    assert (result is not None) == expected


@pytest.mark.parametrize(
    "context, characters, expected",
    [
        # No context, or a non-trigger character request should still trigger
        (None, set(), True),
        (None, {">", "."}, True),
        (types.CompletionContext(types.CompletionTriggerKind.Invoked), set(), True),
        (
            types.CompletionContext(types.CompletionTriggerKind.Invoked),
            {".", "<"},
            True,
        ),
        (
            types.CompletionContext(
                types.CompletionTriggerKind.TriggerForIncompleteCompletions
            ),
            set(),
            True,
        ),
        (
            types.CompletionContext(
                types.CompletionTriggerKind.TriggerForIncompleteCompletions
            ),
            {".", "<"},
            True,
        ),
        (
            types.CompletionContext(
                types.CompletionTriggerKind.TriggerCharacter,
            ),
            set(),
            True,
        ),
        (
            types.CompletionContext(
                types.CompletionTriggerKind.TriggerCharacter,
            ),
            {".", "<"},
            True,
        ),
        (
            types.CompletionContext(
                types.CompletionTriggerKind.TriggerCharacter, trigger_character="."
            ),
            set(),
            True,
        ),
        (
            types.CompletionContext(
                types.CompletionTriggerKind.TriggerCharacter, trigger_character="."
            ),
            {".", ":"},
            True,
        ),
        (
            types.CompletionContext(
                types.CompletionTriggerKind.TriggerCharacter, trigger_character="."
            ),
            {":"},
            False,
        ),
    ],
)
def test_completion_trigger_characters(
    context: Optional[types.CompletionContext], characters: Set[str], expected: bool
):
    """Ensure that ``CompletionTrigger`` responds to the trigger character correctly."""

    uri = server.Uri.parse("file:///test.txt")
    params = types.CompletionParams(
        position=types.Position(line=0, character=0),
        text_document=types.TextDocumentIdentifier(uri=str(uri)),
        context=context,
    )
    document = TextDocument(uri=str(uri), source="some text")

    trigger = server.CompletionTrigger(
        patterns=[re.compile(".*")], characters=characters
    )
    result = trigger(uri, params, document, "rst", types.ClientCapabilities())

    assert (result is not None) == expected


def test_completion_trigger_pattern_no_match():
    """Ensure that if none of the ``CompletionTrigger`` patterns match, the trigger does
    not fire."""

    uri = server.Uri.parse("file:///test.txt")
    params = types.CompletionParams(
        position=types.Position(line=0, character=0),
        text_document=types.TextDocumentIdentifier(uri=str(uri)),
    )
    document = TextDocument(uri=str(uri), source="some text")

    trigger = server.CompletionTrigger(patterns=[re.compile("xx"), re.compile("yy")])
    assert trigger(uri, params, document, "rst", types.ClientCapabilities()) is None


def test_completion_trigger_pattern_match_wrong_pos():
    """Ensure that if one of the ``CompletionTrigger`` patterns match, the trigger does
    not fire if the match is outside of the requested location."""

    uri = server.Uri.parse("file:///test.txt")
    params = types.CompletionParams(
        position=types.Position(line=0, character=0),
        text_document=types.TextDocumentIdentifier(uri=str(uri)),
    )
    document = TextDocument(uri=str(uri), source="some xx text")

    trigger = server.CompletionTrigger(patterns=[re.compile("xx"), re.compile("yy")])
    assert trigger(uri, params, document, "rst", types.ClientCapabilities()) is None


def test_completion_trigger_pattern_match():
    """Ensure that if one of the ``CompletionTrigger`` patterns match, the trigger returns
    the completion context with the correct fields."""

    uri = server.Uri.parse("file:///test.txt")
    params = types.CompletionParams(
        position=types.Position(line=0, character=6),
        text_document=types.TextDocumentIdentifier(uri=str(uri)),
    )
    document = TextDocument(uri=str(uri), source="some xx text")
    client_capabilities = types.ClientCapabilities(
        text_document=types.TextDocumentClientCapabilities(
            completion=types.CompletionClientCapabilities(
                context_support=True,
            ),
        ),
    )

    trigger = server.CompletionTrigger(patterns=[re.compile("xx"), re.compile("yy")])
    result = trigger(uri, params, document, "rst", client_capabilities)

    assert result is not None
    assert result.uri == uri
    assert result.doc == document
    assert result.position == params.position
    assert result.language == "rst"
    assert result.capabilities == client_capabilities

    assert result.match.group(0) == "xx"


def test_completion_trigger_pattern_first_match():
    """Ensure that if more than one of the ``CompletionTrigger`` patterns match, the
    trigger returns the first match."""

    uri = server.Uri.parse("file:///test.txt")
    params = types.CompletionParams(
        position=types.Position(line=0, character=6),
        text_document=types.TextDocumentIdentifier(uri=str(uri)),
    )
    document = TextDocument(uri=str(uri), source="some yy xx text")
    client_capabilities = types.ClientCapabilities(
        text_document=types.TextDocumentClientCapabilities(
            completion=types.CompletionClientCapabilities(
                context_support=True,
            ),
        ),
    )

    trigger = server.CompletionTrigger(
        patterns=[re.compile("some.*xx"), re.compile("yy.*text")]
    )
    result = trigger(uri, params, document, "rst", client_capabilities)

    assert result is not None
    assert result.match.group(0) == "some yy xx"

    trigger = server.CompletionTrigger(
        patterns=[re.compile("yy.*text"), re.compile("some.*xx")]
    )
    result = trigger(uri, params, document, "rst", client_capabilities)

    assert result is not None
    assert result.match.group(0) == "yy xx text"
