from __future__ import annotations

import pathlib
import typing

import pytest
from lsprotocol import types
from pytest_lsp import LanguageClient

if typing.TYPE_CHECKING:
    from typing import Optional
    from typing import Set


EXPECTED = {
    "ref",
    "doc",
    "option",
    "func",
    "class",
    "c:macro",
    "c:func",
    "py:func",
    "py:class",
    "std:ref",
    "std:doc",
}

UNEXPECTED = {
    "macro",
    "restructuredtext-unimplemented-role",
}


LOCAL_PY_CLASSES = {
    "counters.pattern.PatternCounter",
    "counters.pattern.NoMatchesError",
}
PYTHON_PY_CLASSES = {"logging.Filter", "http.server.HTTPServer"}
SPHINX_PY_CLASSES = {"sphinx.addnodes.desc"}


@pytest.mark.parametrize(
    "text, expected, unexpected",
    [
        ("::", None, None),
        (":", EXPECTED, UNEXPECTED),
        (":r", EXPECTED, UNEXPECTED),
        (":c:func", EXPECTED, UNEXPECTED),
        (":c:func: ", None, None),
        ("  ::", None, None),
        ("  :", EXPECTED, UNEXPECTED),
        ("  :r", EXPECTED, UNEXPECTED),
        ("  :c:func", EXPECTED, UNEXPECTED),
        ("  :c:func: ", None, None),
        ("(:", EXPECTED, UNEXPECTED),
        ("(:r", EXPECTED, UNEXPECTED),
        ("(:c:func", EXPECTED, UNEXPECTED),
    ],
)
@pytest.mark.asyncio(scope="session")
async def test_rst_role_completions(
    client: LanguageClient,
    uri_for,
    text: str,
    expected: Optional[Set[str]],
    unexpected: Optional[Set[str]],
):
    """Ensure that the language server can offer role completions in rst documents."""
    test_uri = uri_for("workspaces", "demo", "rst", "roles.rst")

    uri = str(test_uri)
    fpath = pathlib.Path(test_uri)
    contents = fpath.read_text()
    linum = contents.splitlines().index(".. Add your reference here...")

    # Open the file
    client.text_document_did_open(
        types.DidOpenTextDocumentParams(
            text_document=types.TextDocumentItem(
                uri=uri,
                language_id="restructuredtext",
                version=1,
                text=contents,
            )
        )
    )

    # Write some text
    #
    # This should replace the '.. Add your note here...' comment in
    # 'demo/rst/directives.rst' with the provided text
    client.text_document_did_change(
        types.DidChangeTextDocumentParams(
            text_document=types.VersionedTextDocumentIdentifier(uri=uri, version=2),
            content_changes=[
                types.TextDocumentContentChangeEvent_Type1(
                    text=text,
                    range=types.Range(
                        start=types.Position(line=linum, character=0),
                        end=types.Position(line=linum + 1, character=0),
                    ),
                )
            ],
        )
    )

    # Make the completion request
    results = await client.text_document_completion_async(
        types.CompletionParams(
            text_document=types.TextDocumentIdentifier(uri=uri),
            position=types.Position(line=linum, character=len(text)),
        )
    )

    # Close the document - without saving!
    client.text_document_did_close(
        types.DidCloseTextDocumentParams(
            text_document=types.TextDocumentIdentifier(uri=uri)
        )
    )

    if expected is None:
        assert results is None
    else:
        items = {item.label for item in results.items}
        unexpected = unexpected or set()

        assert expected == items & expected
        assert set() == items & unexpected


@pytest.mark.parametrize(
    "text, expected, unexpected",
    [
        (":ref:`", {"genindex", "modindex", "rst-roles-completion"}, set()),
        (":std:ref:`", {"genindex", "modindex", "rst-roles-completion"}, set()),
        (":doc:`", {"demo_myst", "demo_rst", "rst/domains/python"}, set()),
        (":std:doc:`", {"demo_myst", "demo_rst", "rst/domains/python"}, set()),
        (
            ":class:`",
            LOCAL_PY_CLASSES,
            PYTHON_PY_CLASSES | SPHINX_PY_CLASSES,
        ),
        (
            ":py:class:`",
            LOCAL_PY_CLASSES,
            PYTHON_PY_CLASSES | SPHINX_PY_CLASSES,
        ),
        (
            ":external:py:class:`",
            PYTHON_PY_CLASSES | SPHINX_PY_CLASSES,
            LOCAL_PY_CLASSES,
        ),
        (
            ":external+python:py:class:`",
            PYTHON_PY_CLASSES,
            LOCAL_PY_CLASSES | SPHINX_PY_CLASSES,
        ),
        (
            ":external+sphinx:py:class:`",
            SPHINX_PY_CLASSES,
            LOCAL_PY_CLASSES | PYTHON_PY_CLASSES,
        ),
        (":func:`", {"counters.pattern.count_numbers"}, set()),
        (":py:func:`", {"counters.pattern.count_numbers"}, set()),
    ],
)
@pytest.mark.asyncio(scope="session")
async def test_rst_role_target_completions(
    client: LanguageClient,
    uri_for,
    text: str,
    expected: Optional[Set[str]],
    unexpected: Optional[Set[str]],
):
    """Ensure that the language server can offer role target completions in rst
    documents."""
    test_uri = uri_for("workspaces", "demo", "rst", "roles.rst")

    uri = str(test_uri)
    fpath = pathlib.Path(test_uri)
    contents = fpath.read_text()
    linum = contents.splitlines().index(".. Add your reference here...")

    # Open the file
    client.text_document_did_open(
        types.DidOpenTextDocumentParams(
            text_document=types.TextDocumentItem(
                uri=uri,
                language_id="restructuredtext",
                version=1,
                text=contents,
            )
        )
    )

    # Write some text
    #
    # This should replace the '.. Add your note here...' comment in
    # 'demo/rst/directives.rst' with the provided text
    client.text_document_did_change(
        types.DidChangeTextDocumentParams(
            text_document=types.VersionedTextDocumentIdentifier(uri=uri, version=2),
            content_changes=[
                types.TextDocumentContentChangeEvent_Type1(
                    text=text,
                    range=types.Range(
                        start=types.Position(line=linum, character=0),
                        end=types.Position(line=linum + 1, character=0),
                    ),
                )
            ],
        )
    )

    # Make the completion request
    results = await client.text_document_completion_async(
        types.CompletionParams(
            text_document=types.TextDocumentIdentifier(uri=uri),
            position=types.Position(line=linum, character=len(text)),
        )
    )

    # Close the document - without saving!
    client.text_document_did_close(
        types.DidCloseTextDocumentParams(
            text_document=types.TextDocumentIdentifier(uri=uri)
        )
    )

    if expected is None:
        assert results is None
    else:
        items = {item.label for item in results.items}
        unexpected = unexpected or set()

        assert expected == items & expected
        assert set() == items & unexpected


@pytest.mark.parametrize(
    "text, expected, unexpected",
    [
        ("{", EXPECTED, UNEXPECTED),
        ("{r", EXPECTED, UNEXPECTED),
        ("{c:func", EXPECTED, UNEXPECTED),
        ("{c:func} ", None, None),
        ("  {", EXPECTED, UNEXPECTED),
        ("  {r", EXPECTED, UNEXPECTED),
        ("  {c:func", EXPECTED, UNEXPECTED),
        ("  {c:func} ", None, None),
        ("({", EXPECTED, UNEXPECTED),
        ("({r", EXPECTED, UNEXPECTED),
        ("({c:func", EXPECTED, UNEXPECTED),
    ],
)
@pytest.mark.asyncio(scope="session")
async def test_myst_role_completions(
    client: LanguageClient,
    uri_for,
    text: str,
    expected: Optional[Set[str]],
    unexpected: Optional[Set[str]],
):
    """Ensure that the language server can offer completions in MyST documents."""
    test_uri = uri_for("workspaces", "demo", "myst", "roles.md")

    uri = str(test_uri)
    fpath = pathlib.Path(test_uri)
    contents = fpath.read_text()
    linum = contents.splitlines().index("% Add your reference here...")

    # Open the file
    client.text_document_did_open(
        types.DidOpenTextDocumentParams(
            text_document=types.TextDocumentItem(
                uri=uri,
                language_id="markdown",
                version=1,
                text=contents,
            )
        )
    )

    # Write some text
    #
    # This should replace the '% Add your note here...' comment in
    # 'demo/myst/directives.md' with the provided text
    client.text_document_did_change(
        types.DidChangeTextDocumentParams(
            text_document=types.VersionedTextDocumentIdentifier(uri=uri, version=2),
            content_changes=[
                types.TextDocumentContentChangeEvent_Type1(
                    text=text,
                    range=types.Range(
                        start=types.Position(line=linum, character=0),
                        end=types.Position(line=linum + 1, character=0),
                    ),
                )
            ],
        )
    )

    # Make the completion request
    results = await client.text_document_completion_async(
        types.CompletionParams(
            text_document=types.TextDocumentIdentifier(uri=uri),
            position=types.Position(line=linum, character=len(text)),
        )
    )

    # Close the document - without saving!
    client.text_document_did_close(
        types.DidCloseTextDocumentParams(
            text_document=types.TextDocumentIdentifier(uri=uri)
        )
    )

    if expected is None:
        assert results is None
    else:
        items = {item.label for item in results.items}
        unexpected = unexpected or set()

        assert expected == items & expected
        assert set() == items & unexpected


@pytest.mark.parametrize(
    "text, expected, unexpected",
    [
        ("{ref}`", {"genindex", "modindex", "rst-roles-completion"}, set()),
        ("{std:ref}`", {"genindex", "modindex", "rst-roles-completion"}, set()),
        ("{doc}`", {"demo_myst", "demo_rst", "rst/domains/python"}, set()),
        ("{std:doc}`", {"demo_myst", "demo_rst", "rst/domains/python"}, set()),
        (
            "{class}`",
            LOCAL_PY_CLASSES,
            PYTHON_PY_CLASSES | SPHINX_PY_CLASSES,
        ),
        (
            "{py:class}`",
            LOCAL_PY_CLASSES,
            PYTHON_PY_CLASSES | SPHINX_PY_CLASSES,
        ),
        (
            "{external:py:class}`",
            PYTHON_PY_CLASSES | SPHINX_PY_CLASSES,
            LOCAL_PY_CLASSES,
        ),
        (
            "{external+sphinx:py:class}`",
            SPHINX_PY_CLASSES,
            LOCAL_PY_CLASSES | PYTHON_PY_CLASSES,
        ),
        (
            "{external+python:py:class}`",
            PYTHON_PY_CLASSES,
            LOCAL_PY_CLASSES | SPHINX_PY_CLASSES,
        ),
        ("{func}`", {"counters.pattern.count_numbers"}, set()),
        ("{py:func}`", {"counters.pattern.count_numbers"}, set()),
    ],
)
@pytest.mark.asyncio(scope="session")
async def test_myst_role_target_completions(
    client: LanguageClient,
    uri_for,
    text: str,
    expected: Optional[Set[str]],
    unexpected: Optional[Set[str]],
):
    """Ensure that the language server can offer completions in MyST documents."""
    test_uri = uri_for("workspaces", "demo", "myst", "roles.md")

    uri = str(test_uri)
    fpath = pathlib.Path(test_uri)
    contents = fpath.read_text()
    linum = contents.splitlines().index("% Add your reference here...")

    # Open the file
    client.text_document_did_open(
        types.DidOpenTextDocumentParams(
            text_document=types.TextDocumentItem(
                uri=uri,
                language_id="markdown",
                version=1,
                text=contents,
            )
        )
    )

    # Write some text
    #
    # This should replace the '% Add your note here...' comment in
    # 'demo/myst/directives.md' with the provided text
    client.text_document_did_change(
        types.DidChangeTextDocumentParams(
            text_document=types.VersionedTextDocumentIdentifier(uri=uri, version=2),
            content_changes=[
                types.TextDocumentContentChangeEvent_Type1(
                    text=text,
                    range=types.Range(
                        start=types.Position(line=linum, character=0),
                        end=types.Position(line=linum + 1, character=0),
                    ),
                )
            ],
        )
    )

    # Make the completion request
    results = await client.text_document_completion_async(
        types.CompletionParams(
            text_document=types.TextDocumentIdentifier(uri=uri),
            position=types.Position(line=linum, character=len(text)),
        )
    )

    # Close the document - without saving!
    client.text_document_did_close(
        types.DidCloseTextDocumentParams(
            text_document=types.TextDocumentIdentifier(uri=uri)
        )
    )

    if expected is None:
        assert results is None
    else:
        items = {item.label for item in results.items}
        unexpected = unexpected or set()

        assert expected == items & expected
        assert set() == items & unexpected
