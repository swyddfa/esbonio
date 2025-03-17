from __future__ import annotations

import pathlib

import pytest
from lsprotocol import types
from pytest_lsp import LanguageClient

EXPECTED = {
    "function",
    "module",
    "option",
    "program",
    "image",
    "toctree",
    "c:macro",
    "c:function",
    "py:function",
    "py:module",
    "std:program",
    "std:option",
}

RST_EXPECTED = EXPECTED.copy()
MYST_EXPECTED = {"eval-rst", *EXPECTED}

UNEXPECTED = {
    "macro",
    "restructuredtext-test-directive",
}

RST_UNEXPECTED = {"eval-rst", *UNEXPECTED}
MYST_UNEXPECTED = UNEXPECTED.copy()

# Code blocks
LEXERS = {"python", "python-console", "nix"}

# Filepaths
ROOT_FILES = {"conf.py", "index.rst", "myst", "rst"}
RST_FILES = {"directives.rst", "roles.rst", "domains"}
MYST_FILES = {"directives.md", "roles.md"}


@pytest.mark.parametrize(
    "text, expected, unexpected",
    [
        # Test cases covering directive name completion
        (".", None, None),
        ("..", RST_EXPECTED, RST_UNEXPECTED),
        (".. ", RST_EXPECTED, RST_UNEXPECTED),
        (".. d", RST_EXPECTED, RST_UNEXPECTED),
        (".. code-b", RST_EXPECTED, RST_UNEXPECTED),
        (".. codex-block:: ", None, None),
        (".. c:", RST_EXPECTED, RST_UNEXPECTED),
        (".. _some_label:", None, None),
        ("   .", None, None),
        ("   ..", RST_EXPECTED, RST_UNEXPECTED),
        ("   .. ", RST_EXPECTED, RST_UNEXPECTED),
        ("   .. d", RST_EXPECTED, RST_UNEXPECTED),
        ("   .. doctest:: ", None, None),
        ("   .. code-b", RST_EXPECTED, RST_UNEXPECTED),
        ("   .. codex-block:: ", None, None),
        ("   .. _some_label:", None, None),
        ("   .. c:", RST_EXPECTED, RST_UNEXPECTED),
        # Test cases covering directive argument completion for...
        #
        # -- pygments lexers
        (".. code-block:: ", LEXERS, None),
        (".. highlight:: ", LEXERS, None),
        (".. sourcecode:: ", LEXERS, None),
        # -- filepaths
        (".. image:: /", ROOT_FILES, None),
        (".. image:: ../", ROOT_FILES, None),
        (".. image:: ", RST_FILES, None),
        (".. image:: .", RST_FILES, None),
        (".. image:: ./", RST_FILES, None),
        (".. figure:: ./", RST_FILES, None),
        (".. include:: ./", RST_FILES, None),
        (".. literalinclude:: ./", RST_FILES, None),
    ],
)
@pytest.mark.asyncio(loop_scope="session")
async def test_rst_directive_completions(
    client: LanguageClient,
    uri_for,
    text: str,
    expected: set[str] | None,
    unexpected: set[str] | None,
):
    """Ensure that the language server can offer directive completions in rst
    documents."""
    test_uri = uri_for("workspaces", "demo", "rst", "directives.rst")

    uri = str(test_uri)
    fpath = pathlib.Path(test_uri)
    contents = fpath.read_text()
    linum = contents.splitlines().index(".. Add your note here...")

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
                types.TextDocumentContentChangePartial(
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
        # Test cases covering directive name completions
        ("`", None, None),
        ("``", None, None),
        # -- Unless the user types a '{', we should suggest languauge names
        ("```", LEXERS, MYST_EXPECTED | MYST_UNEXPECTED),
        ("```{", MYST_EXPECTED, MYST_UNEXPECTED),
        ("```{d", MYST_EXPECTED, MYST_UNEXPECTED),
        ("```{code-b", MYST_EXPECTED, MYST_UNEXPECTED),
        ("```{codex-block} ", None, None),
        ("```{c:", MYST_EXPECTED, MYST_UNEXPECTED),
        ("   `", None, None),
        ("   ``", None, None),
        # -- Unless the user types a '{', we should suggest languauge names
        ("   ```", LEXERS, MYST_EXPECTED | MYST_UNEXPECTED),
        ("   ```{", MYST_EXPECTED, MYST_UNEXPECTED),
        ("   ```{d", MYST_EXPECTED, MYST_UNEXPECTED),
        ("   ```{doctest}", None, None),
        ("   ```{code-b", MYST_EXPECTED, MYST_UNEXPECTED),
        ("   ```{codex-block}", None, None),
        ("   ```{c:", MYST_EXPECTED, MYST_UNEXPECTED),
        # Test cases covering directive argument completions for...
        #
        # -- pygments lexers
        ("```{code-block} ", LEXERS, None),
        ("```{highlight} ", LEXERS, None),
        ("```{sourcecode} ", LEXERS, None),
        # -- filepaths
        ("```{image} /", ROOT_FILES, None),
        ("```{image} ../", ROOT_FILES, None),
        ("```{image} ", MYST_FILES, None),
        ("```{image} .", MYST_FILES, None),
        ("```{image} ./", MYST_FILES, None),
        ("```{figure} ./", MYST_FILES, None),
        ("```{include} ./", MYST_FILES, None),
        ("```{literalinclude} ./", MYST_FILES, None),
    ],
)
@pytest.mark.asyncio(loop_scope="session")
async def test_myst_directive_completions(
    client: LanguageClient,
    uri_for,
    text: str,
    expected: set[str] | None,
    unexpected: set[str] | None,
):
    """Ensure that the language server can offer completions in MyST documents."""
    test_uri = uri_for("workspaces", "demo", "myst", "directives.md")

    uri = str(test_uri)
    fpath = pathlib.Path(test_uri)
    contents = fpath.read_text()
    linum = contents.splitlines().index("% Add your note here...")

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
                types.TextDocumentContentChangePartial(
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


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize(
    "filename,expected",
    [
        (
            ["workspaces", "demo", "rst", "directives.rst"],
            [
                types.DocumentLink(
                    target="${ROOT}/rst/directives.rst",
                    tooltip="Path exists",
                    range=types.Range(
                        start=types.Position(line=49, character=18),
                        end=types.Position(line=49, character=34),
                    ),
                ),
                types.DocumentLink(
                    target="${ROOT}/rst/symbols.rst",
                    tooltip="Path exists",
                    range=types.Range(
                        start=types.Position(line=63, character=18),
                        end=types.Position(line=63, character=31),
                    ),
                ),
                types.DocumentLink(
                    target="https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html#rst-directives",
                    tooltip="Directives - Sphinx v",  # don't check for a precise version!
                    range=types.Range(
                        start=types.Position(line=3, character=121),
                        end=types.Position(line=3, character=135),
                    ),
                ),
                types.DocumentLink(
                    target="https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-literalinclude",
                    tooltip="literalinclude - Sphinx v",
                    range=types.Range(
                        start=types.Position(line=21, character=28),
                        end=types.Position(line=21, character=42),
                    ),
                ),
                types.DocumentLink(
                    target="https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-code",
                    tooltip="code - Sphinx v",
                    range=types.Range(
                        start=types.Position(line=30, character=28),
                        end=types.Position(line=30, character=32),
                    ),
                ),
                types.DocumentLink(
                    target="https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-code-block",
                    tooltip="code-block - Sphinx v",
                    range=types.Range(
                        start=types.Position(line=31, character=28),
                        end=types.Position(line=31, character=38),
                    ),
                ),
                types.DocumentLink(
                    target="https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-highlight",
                    tooltip="highlight - Sphinx v",
                    range=types.Range(
                        start=types.Position(line=32, character=28),
                        end=types.Position(line=32, character=37),
                    ),
                ),
                types.DocumentLink(
                    target="https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-sourcecode",
                    tooltip="sourcecode - Sphinx v",
                    range=types.Range(
                        start=types.Position(line=33, character=28),
                        end=types.Position(line=33, character=38),
                    ),
                ),
            ],
        ),
        (
            ["workspaces", "demo", "myst", "directives.md"],
            [
                types.DocumentLink(
                    target="${ROOT}/myst/directives.md",
                    tooltip="Path exists",
                    range=types.Range(
                        start=types.Position(line=47, character=15),
                        end=types.Position(line=47, character=30),
                    ),
                ),
                types.DocumentLink(
                    target="${ROOT}/myst/symbols.md",
                    tooltip="Path exists",
                    range=types.Range(
                        start=types.Position(line=59, character=15),
                        end=types.Position(line=59, character=27),
                    ),
                ),
                types.DocumentLink(
                    target="https://myst-parser.readthedocs.io/en/latest/syntax/roles-and-directives.html#syntax-directives",
                    tooltip="Directives - a block-level extension point - MyST Parser v",
                    range=types.Range(
                        start=types.Position(line=2, character=126),
                        end=types.Position(line=2, character=143),
                    ),
                ),
                types.DocumentLink(
                    target="https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-literalinclude",
                    tooltip="literalinclude - Sphinx v",  # don't check for a precise version!
                    range=types.Range(
                        start=types.Position(line=19, character=28),
                        end=types.Position(line=19, character=42),
                    ),
                ),
                types.DocumentLink(
                    target="https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-code",
                    tooltip="code - Sphinx v",
                    range=types.Range(
                        start=types.Position(line=28, character=28),
                        end=types.Position(line=28, character=32),
                    ),
                ),
                types.DocumentLink(
                    target="https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-code-block",
                    tooltip="code-block - Sphinx v",
                    range=types.Range(
                        start=types.Position(line=29, character=28),
                        end=types.Position(line=29, character=38),
                    ),
                ),
                types.DocumentLink(
                    target="https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-highlight",
                    tooltip="highlight - Sphinx v",
                    range=types.Range(
                        start=types.Position(line=30, character=28),
                        end=types.Position(line=30, character=37),
                    ),
                ),
                types.DocumentLink(
                    target="https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-sourcecode",
                    tooltip="sourcecode - Sphinx v",
                    range=types.Range(
                        start=types.Position(line=31, character=28),
                        end=types.Position(line=31, character=38),
                    ),
                ),
            ],
        ),
    ],
)
async def test_directive_document_links(
    client: LanguageClient,
    uri_for,
    filename: list[str],
    expected: list[types.DocumentLink],
):
    """Ensure that we handle ``textDocument/documentLink`` requests correctly."""

    root_uri = str(uri_for("workspaces", "demo"))
    test_uri = uri_for(*filename)

    links = await client.text_document_document_link_async(
        types.DocumentLinkParams(
            text_document=types.TextDocumentIdentifier(uri=str(test_uri))
        )
    )

    assert len(links) == len(expected)

    for link, actual in zip(expected, links):
        assert link.range == actual.range

        target = link.target.replace("${ROOT}", root_uri)
        assert target == actual.target

        if link.tooltip is not None:
            assert actual.tooltip.startswith(link.tooltip)


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize(
    "filename,position,expected",
    [
        (
            ["workspaces", "demo", "rst", "directives.rst"],
            # Requests for the diretive itself should return nothing
            types.Position(line=63, character=12),
            None,
        ),
        (
            ["workspaces", "demo", "rst", "directives.rst"],
            types.Position(line=63, character=22),
            [
                types.Location(
                    uri="${ROOT}/rst/symbols.rst",
                    range=types.Range(
                        start=types.Position(line=0, character=0),
                        end=types.Position(line=1, character=0),
                    ),
                )
            ],
        ),
        (
            ["workspaces", "demo", "myst", "directives.md"],
            # Requests for the diretive itself should return nothing
            types.Position(line=59, character=11),
            None,
        ),
        (
            ["workspaces", "demo", "myst", "directives.md"],
            types.Position(line=59, character=21),
            [
                types.Location(
                    uri="${ROOT}/myst/symbols.md",
                    range=types.Range(
                        start=types.Position(line=0, character=0),
                        end=types.Position(line=1, character=0),
                    ),
                )
            ],
        ),
    ],
)
async def test_directive_argument_definitions(
    client: LanguageClient,
    uri_for,
    filename: list[str],
    position: types.Position,
    expected: list[types.Location] | None,
):
    """Ensure that we handle ``textDocument/definition`` requests correctly for
    directive arguments."""

    root_uri = str(uri_for("workspaces", "demo"))
    test_uri = uri_for(*filename)

    fpath = pathlib.Path(test_uri)
    contents = fpath.read_text()

    # Open the file - needed so that esbonio can correctly determine the language_id of
    # the document. Strictly speaking, you could probably consider the fact that this is
    # necessary to be a bug... but 99% of the time I'm fairly sure the client will have
    # done this before making the goto definition call.
    client.text_document_did_open(
        types.DidOpenTextDocumentParams(
            text_document=types.TextDocumentItem(
                uri=str(test_uri),
                language_id="restructuredtext"
                if fpath.suffix == ".rst"
                else "markdown",
                version=1,
                text=contents,
            )
        )
    )

    definitions = await client.text_document_definition_async(
        types.DefinitionParams(
            text_document=types.TextDocumentIdentifier(uri=str(test_uri)),
            position=position,
        )
    )

    if expected is None:
        assert definitions is None

    else:
        assert len(definitions) == len(expected)

        location: types.Location
        for location, actual in zip(expected, definitions):
            expected_uri = location.uri.replace("${ROOT}", root_uri)
            assert expected_uri == actual.uri
            assert location.range == actual.range
