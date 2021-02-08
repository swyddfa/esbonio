import logging
import itertools
import pathlib
import time

from typing import Set

import py.test

from pygls.features import (
    COMPLETION,
    INITIALIZE,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_OPEN,
)
from pygls.server import LanguageServer
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

WAIT = 0.1  # How long should we sleep after an lsp.notify(...)


def do_completion_test(
    client: LanguageServer,
    server: LanguageServer,
    root: pathlib.Path,
    filename: str,
    text: str,
    expected: Set[str],
    insert_newline: bool = True,
):
    """A generic helper for performing completion tests.

    Being an integration test, it is quite involved as it has to use the protocol to
    take the server to a point where it can provide completion suggestions. As part of
    the setup, this helper

    - Sends an 'initialize' request to the server, setting the workspace root.
    - Sends a 'textDocument/didOpen' notification, loading the specified document in the
      server's workspace
    - Sends a 'textDocument/didChange' notification, inserting the text we want
      suggestions for
    - Sends a 'completion' request, and ensures that the expected completed items are in
      the response

    Currently this method is only capable of ensuring that item labels are as expected,
    none of the other CompletionItem fields are inspected. This method is also not capable
    of ensuring particular items are NOT suggested.

    Parameters
    ----------
    client:
        The client LanguageServer instance
    server:
        The server LanguageServer instance
    root:
        The directory to use as the workspace root
    filename:
        The file to open for the test, relative to the workspace root
    text:
        The text to insert, this is the text this method requests completions for.
        Note this CANNOT contain any newlines.
    expected:
        The CompletionItem labels that should be returned. This does not have to be
        exhaustive.
    insert_newline:
        Flag to indicate if a newline should be inserted before the given ``text``
    """

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
    testfile = root / filename
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
    start = len(content.splitlines()) + insert_newline
    text = "\n" + text if insert_newline else text

    client.lsp.notify(
        TEXT_DOCUMENT_DID_CHANGE,
        DidChangeTextDocumentParams(
            VersionedTextDocumentIdentifier(testuri, 2),
            [
                TextDocumentContentChangeEvent(
                    Range(Position(start, 0), Position(start, 0)), text=text
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


def intersphinx_patterns(rolename, namespace):
    return [
        s.format(rolename, namespace)
        for s in [
            ":{}:`{}:",
            ":{}:`More Info <{}:",
            "   :{}:`{}:",
            "   :{}:`Some Label <{}:",
        ]
    ]


@py.test.mark.integration
@py.test.mark.parametrize(
    "text,setup",
    [
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
        *itertools.product(
            intersphinx_patterns("ref", "python"),
            [
                ("sphinx-default", set()),
                (
                    "sphinx-extensions",
                    {"configparser-objects", "types", "whatsnew-index"},
                ),
            ],
        ),
        *itertools.product(
            intersphinx_patterns("class", "python"),
            [
                ("sphinx-default", set()),
                (
                    "sphinx-extensions",
                    {"abc.ABCMeta", "logging.StreamHandler", "zipfile.ZipInfo"},
                ),
            ],
        ),
        *itertools.product(
            intersphinx_patterns("ref", "sphinx"),
            [
                ("sphinx-default", set()),
                (
                    "sphinx-extensions",
                    {
                        "basic-domain-markup",
                        "extension-tutorials-index",
                        "writing-builders",
                    },
                ),
            ],
        ),
        *itertools.product(
            intersphinx_patterns("class", "sphinx"),
            [
                ("sphinx-default", set()),
                (
                    "sphinx-extensions",
                    {
                        "sphinx.addnodes.desc",
                        "sphinx.builders.Builder",
                        "sphinxcontrib.websupport.WebSupport",
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

    do_completion_test(client, server, root, "index.rst", text, expected)


def test_expected_directive_option_completions(client_server, testdata, caplog):
    """Ensure that we can handle directive option completions."""

    caplog.set_level(logging.INFO)

    client, server = client_server
    root = testdata("sphinx-default", path_only=True)
    expected = {"align", "alt", "class", "height", "name", "scale", "target", "width"}

    do_completion_test(
        client,
        server,
        root,
        "directive_options.rst",
        "   :a",
        expected,
        insert_newline=False,
    )
