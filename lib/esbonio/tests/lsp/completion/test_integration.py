import itertools
import time

import py.test

from pygls.features import (
    COMPLETION,
    INITIALIZE,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_OPEN,
)
from pygls.types import (
    CompletionContext,
    CompletionParams,
    CompletionTriggerKind,
    DidChangeTextDocumentParams,
    DidOpenTextDocumentParams,
    Position,
    Range,
    TextDocumentContentChangeEvent,
    TextDocumentIdentifier,
    TextDocumentItem,
    VersionedTextDocumentIdentifier,
)

WAIT = 0.1

# Expected directive suggestions (not exhaustive)
DIRECTIVES = {
    "admonition",
    "attention",
    "attribute",
    "classmethod",
    "code-block",
    "envvar",
    "figure",
    "glossary",
    "hlist",
    "image",
    "include",
    "index",
    "line-block",
    "list-table",
    "literalinclude",
    "toctree",
}

# Expected role suggestions (not exhaustive)
ROLES = {"class", "doc", "func", "ref", "term"}


# Expected (:py):class: target suggestions
CLASS_TARGETS = {"pythagoras.Triangle"}

# Expected :doc: target suggestions
DOC_TARGETS = {"index", "glossary", "theorems/index", "theorems/pythagoras"}

# Expected (:py):func: target suggestions
FUNC_TARGETS = {"pythagoras.calc_hypotenuse", "pythagoras.calc_side"}

# Expected (:py):meth: target suggestions
METH_TARGETS = {"pythagoras.Triangle.is_right_angled"}

# Expected :ref: target suggestions
REF_TARGETS = {
    "genindex",
    "modindex",
    "py-modindex",
    "pythagoras_theorem",
    "search",
    "welcome",
}


def role_target_examples(rolename):
    return [
        s.format(rolename)
        for s in [
            ":{}:`",
            ":{}:`More Info <",
            "   :{}:`",
            "   :{}:`Some Label <",
        ]
    ]


@py.test.mark.integration
@py.test.mark.parametrize(
    "text,expected",
    [
        *itertools.product(
            [
                ".",
                ".. doctest::",
                ".. code-block::",
                "   .",
                "   .. doctest::",
                "   .. code-block::",
                ".. _some_label:",
                "   .. _some_label:",
            ],
            [set()],
        ),
        *itertools.product(
            [
                "..",
                ".. ",
                ".. d",
                ".. code-b",
                "   ..",
                "   .. ",
                "   .. d",
                "   .. code-b",
            ],
            [DIRECTIVES],
        ),
        *itertools.product(
            [
                ":",
                ":r",
                "some text :",
                "   :",
                "   :r",
                "   some text :",
            ],
            [ROLES],
        ),
        *itertools.product(
            role_target_examples("class"),
            [CLASS_TARGETS],
        ),
        *itertools.product(
            role_target_examples("doc"),
            [DOC_TARGETS],
        ),
        *itertools.product(
            role_target_examples("func"),
            [FUNC_TARGETS],
        ),
        *itertools.product(
            role_target_examples("meth"),
            [METH_TARGETS],
        ),
        *itertools.product(
            role_target_examples("obj"),
            [CLASS_TARGETS, FUNC_TARGETS, METH_TARGETS],
        ),
        *itertools.product(
            role_target_examples("ref"),
            [REF_TARGETS],
        ),
    ],
)
def test_completion(client_server, testdata, text, expected):
    """Ensure that we can offer the correct completion suggestions."""

    client, server = client_server
    root = testdata("sphinx-default", path_only=True)

    # Initialize the language server.
    response = client.lsp.send_request(
        INITIALIZE, {"processId": 1234, "rootUri": root.as_uri(), "capabilities": None}
    ).result(timeout=2)

    # Ensure that the server has configured itself correctly.
    assert server.workspace.root_uri == root.as_uri()

    # Ensure that server broadcasted the fact that it supports completions.
    provider = response.capabilities.completionProvider
    assert set(provider.triggerCharacters) == {".", ":", "`", "<"}

    # Let the server know that we have recevied the response.
    #    client.lsp.notify(INITIALIZED)
    #    time.sleep(WAIT)

    # Let's open a file to edit.
    testfile = root / "index.rst"
    testuri = testfile.as_uri()
    content = testfile.read_text()

    client.lsp.notify(
        TEXT_DOCUMENT_DID_OPEN,
        DidOpenTextDocumentParams(TextDocumentItem(testuri, "rst", 1, content)),
    )

    time.sleep(WAIT)
    assert len(server.lsp.workspace.documents) == 1

    # With the setup out of the way, let's type the text we want completion suggestions
    # for
    start = len(content.splitlines()) + 1

    client.lsp.notify(
        TEXT_DOCUMENT_DID_CHANGE,
        DidChangeTextDocumentParams(
            VersionedTextDocumentIdentifier(testuri, 2),
            [
                TextDocumentContentChangeEvent(
                    Range(Position(start, 0), Position(start, 0)), text="\n" + text
                )
            ],
        ),
    )

    time.sleep(WAIT)
    # Now make the completion request and check to make sure we get the appropriate
    # response
    response = client.lsp.send_request(
        COMPLETION,
        CompletionParams(
            TextDocumentIdentifier(testuri),
            Position(start, len(text) + 1),
            CompletionContext(trigger_kind=CompletionTriggerKind.Invoked),
        ),
    ).result(timeout=2)

    actual = {item.label for item in response.items}
    missing = expected - actual

    assert len(missing) == 0, "Missing expected items, {}".format(missing)
