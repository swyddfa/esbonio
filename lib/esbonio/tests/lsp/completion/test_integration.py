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


def do_completion_test(client, server, root, text, expected):
    """The actual implementation of the completion test"""

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


def role_target_patterns(rolename):
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
    "text,setup",
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
            [("sphinx-default", set())],
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
            [
                (
                    "sphinx-default",
                    {"admonition", "classmethod", "code-block", "image", "toctree"},
                ),
                (
                    "sphinx-extensions",
                    {
                        "admonition",
                        "classmethod",
                        "code-block",
                        "doctest",
                        "image",
                        "testsetup",
                        "toctree",
                    },
                ),
            ],
        ),
        *itertools.product(
            [":", ":r", "some text :", "   :", "   :r", "   some text :"],
            [
                ("sphinx-default", {"class", "doc", "func", "ref", "term"}),
            ],
        ),
        *itertools.product(
            role_target_patterns("class"),
            [
                ("sphinx-default", {"pythagoras.Triangle"}),
                ("sphinx-extensions", {"pythagoras.Triangle", "python", "sphinx"}),
            ],
        ),
        *itertools.product(
            role_target_patterns("doc"),
            [
                (
                    "sphinx-default",
                    {"index", "glossary", "theorems/index", "theorems/pythagoras"},
                ),
                (
                    "sphinx-extensions",
                    {
                        "index",
                        "glossary",
                        "python",
                        "sphinx",
                        "theorems/index",
                        "theorems/pythagoras",
                    },
                ),
            ],
        ),
        *itertools.product(
            role_target_patterns("func"),
            [
                (
                    "sphinx-default",
                    {"pythagoras.calc_hypotenuse", "pythagoras.calc_side"},
                ),
                (
                    "sphinx-extensions",
                    {
                        "pythagoras.calc_hypotenuse",
                        "pythagoras.calc_side",
                        "python",
                        "sphinx",
                    },
                ),
            ],
        ),
        *itertools.product(
            role_target_patterns("meth"),
            [
                ("sphinx-default", {"pythagoras.Triangle.is_right_angled"}),
                (
                    "sphinx-extensions",
                    {"pythagoras.Triangle.is_right_angled", "python", "sphinx"},
                ),
            ],
        ),
        *itertools.product(
            role_target_patterns("obj"),
            [
                (
                    "sphinx-default",
                    {
                        "pythagoras.Triangle",
                        "pythagoras.Triangle.is_right_angled",
                        "pythagoras.calc_hypotenuse",
                        "pythagoras.calc_side",
                    },
                ),
                (
                    "sphinx-extensions",
                    {
                        "pythagoras.Triangle",
                        "pythagoras.Triangle.is_right_angled",
                        "pythagoras.calc_hypotenuse",
                        "pythagoras.calc_side",
                        "python",
                        "sphinx",
                    },
                ),
            ],
        ),
        *itertools.product(
            role_target_patterns("ref"),
            [
                (
                    "sphinx-default",
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
                    "sphinx-extensions",
                    {
                        "genindex",
                        "modindex",
                        "py-modindex",
                        "pythagoras_theorem",
                        "python",
                        "sphinx",
                        "search",
                        "welcome",
                    },
                ),
            ],
        ),
    ],
)
def test_expected_completions(client_server, testdata, text, setup):
    """Ensure that we can offer the correct completion suggestions."""

    client, server = client_server
    project, expected = setup
    root = testdata(project, path_only=True)

    do_completion_test(client, server, root, text, expected)
