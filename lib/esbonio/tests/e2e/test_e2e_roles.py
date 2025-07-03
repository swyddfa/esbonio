from __future__ import annotations

import pathlib

import pytest
from lsprotocol import types
from pytest_lsp import LanguageClient

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
@pytest.mark.asyncio(loop_scope="session")
async def test_rst_role_completions(
    client: LanguageClient,
    uri_for,
    text: str,
    expected: set[str] | None,
    unexpected: set[str] | None,
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
        (":ref:`", {"genindex", "modindex", "rst-roles-completion"}, set()),
        (":std:ref:`", {"genindex", "modindex", "rst-roles-completion"}, set()),
        (":doc:`", {"demo_myst", "demo_rst", "rst/domains/python"}, set()),
        (":std:doc:`", {"demo_myst", "demo_rst", "rst/domains/python"}, set()),
        (
            ":download:`./",
            {"roles.rst", "directives.rst", "domains", "domains.rst"},
            set(),
        ),
        (":download:`../", {"conf.py", "demo_rst.rst", "demo_myst.md"}, set()),
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
@pytest.mark.asyncio(loop_scope="session")
async def test_rst_role_target_completions(
    client: LanguageClient,
    uri_for,
    text: str,
    expected: set[str] | None,
    unexpected: set[str] | None,
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
@pytest.mark.asyncio(loop_scope="session")
async def test_myst_role_completions(
    client: LanguageClient,
    uri_for,
    text: str,
    expected: set[str] | None,
    unexpected: set[str] | None,
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
        ("{ref}`", {"genindex", "modindex", "rst-roles-completion"}, set()),
        ("{std:ref}`", {"genindex", "modindex", "rst-roles-completion"}, set()),
        ("{doc}`", {"demo_myst", "demo_rst", "rst/domains/python"}, set()),
        ("{std:doc}`", {"demo_myst", "demo_rst", "rst/domains/python"}, set()),
        ("{download}`./", {"roles.md", "directives.md"}, set()),
        ("{download}`../", {"conf.py", "demo_rst.rst", "demo_myst.md"}, set()),
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
@pytest.mark.asyncio(loop_scope="session")
async def test_myst_role_target_completions(
    client: LanguageClient,
    uri_for,
    text: str,
    expected: set[str] | None,
    unexpected: set[str] | None,
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
            ["workspaces", "demo", "rst", "roles.rst"],
            [
                types.DocumentLink(
                    target="https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html#rst-roles",
                    tooltip="Roles - Sphinx v",  # don't check for a precise version!
                    range=types.Range(
                        start=types.Position(line=3, character=121),
                        end=types.Position(line=3, character=130),
                    ),
                ),
                types.DocumentLink(
                    target="https://www.sphinx-doc.org/en/master/usage/referencing.html#role-doc",
                    tooltip="doc - Sphinx v",
                    range=types.Range(
                        start=types.Position(line=16, character=45),
                        end=types.Position(line=16, character=48),
                    ),
                ),
                types.DocumentLink(
                    target="https://www.sphinx-doc.org/en/master/usage/referencing.html#role-download",
                    tooltip="download - Sphinx v",
                    range=types.Range(
                        start=types.Position(line=17, character=46),
                        end=types.Position(line=17, character=54),
                    ),
                ),
                types.DocumentLink(
                    target="https://www.sphinx-doc.org/en/master/usage/domains/python.html#role-py-class",
                    tooltip="py:class - Sphinx v",
                    range=types.Range(
                        start=types.Position(line=18, character=52),
                        end=types.Position(line=18, character=60),
                    ),
                ),
                types.DocumentLink(
                    target="https://www.sphinx-doc.org/en/master/usage/domains/python.html#role-py-func",
                    tooltip="py:func - Sphinx v",
                    range=types.Range(
                        start=types.Position(line=18, character=83),
                        end=types.Position(line=18, character=90),
                    ),
                ),
                types.DocumentLink(
                    target="https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html#role-external",
                    tooltip="external - Sphinx v",
                    range=types.Range(
                        start=types.Position(line=19, character=84),
                        end=types.Position(line=19, character=92),
                    ),
                ),
                types.DocumentLink(
                    target="https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html#ext-intersphinx",
                    tooltip="sphinx.ext.intersphinx – Link to other projects’ documentation - Sphinx v",
                    range=types.Range(
                        start=types.Position(line=20, character=25),
                        end=types.Position(line=20, character=40),
                    ),
                ),
                types.DocumentLink(
                    target="${ROOT}/myst/roles.md",
                    range=types.Range(
                        start=types.Position(line=32, character=34),
                        end=types.Position(line=32, character=45),
                    ),
                ),
                types.DocumentLink(
                    target="${ROOT}/rst/roles.rst",
                    tooltip="Path exists",
                    range=types.Range(
                        start=types.Position(line=33, character=25),
                        end=types.Position(line=33, character=36),
                    ),
                ),
                types.DocumentLink(
                    target="https://docs.python.org/3/howto/logging.html#logging-exceptions",
                    tooltip="Exceptions raised during logging - Python v",
                    range=types.Range(
                        start=types.Position(line=34, character=49),
                        end=types.Position(line=34, character=67),
                    ),
                ),
                types.DocumentLink(
                    target="${ROOT}/rst/roles.rst",
                    tooltip="Path exists",
                    range=types.Range(
                        start=types.Position(line=46, character=25),
                        end=types.Position(line=46, character=36),
                    ),
                ),
                types.DocumentLink(
                    target="${ROOT}/myst/roles.md",
                    range=types.Range(
                        start=types.Position(line=47, character=18),
                        end=types.Position(line=47, character=29),
                    ),
                ),
            ],
        ),
        (
            ["workspaces", "demo", "myst", "roles.md"],
            [
                types.DocumentLink(
                    target="https://myst-parser.readthedocs.io/en/latest/syntax/roles-and-directives.html#syntax-roles",
                    tooltip="Roles - an in-line extension point - MyST Parser v",  # don't check for a precise version!
                    range=types.Range(
                        start=types.Position(line=2, character=121),
                        end=types.Position(line=2, character=133),
                    ),
                ),
                types.DocumentLink(
                    target="https://www.sphinx-doc.org/en/master/usage/referencing.html#role-doc",
                    tooltip="doc - Sphinx v",
                    range=types.Range(
                        start=types.Position(line=13, character=45),
                        end=types.Position(line=13, character=48),
                    ),
                ),
                types.DocumentLink(
                    target="https://www.sphinx-doc.org/en/master/usage/referencing.html#role-download",
                    tooltip="download - Sphinx v",
                    range=types.Range(
                        start=types.Position(line=14, character=46),
                        end=types.Position(line=14, character=54),
                    ),
                ),
                types.DocumentLink(
                    target="https://www.sphinx-doc.org/en/master/usage/domains/python.html#role-py-class",
                    tooltip="py:class - Sphinx v",
                    range=types.Range(
                        start=types.Position(line=15, character=52),
                        end=types.Position(line=15, character=60),
                    ),
                ),
                types.DocumentLink(
                    target="https://www.sphinx-doc.org/en/master/usage/domains/python.html#role-py-func",
                    tooltip="py:func - Sphinx v",
                    range=types.Range(
                        start=types.Position(line=15, character=83),
                        end=types.Position(line=15, character=90),
                    ),
                ),
                types.DocumentLink(
                    target="https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html#role-external",
                    tooltip="external - Sphinx v",
                    range=types.Range(
                        start=types.Position(line=16, character=84),
                        end=types.Position(line=16, character=92),
                    ),
                ),
                types.DocumentLink(
                    target="https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html#ext-intersphinx",
                    tooltip="sphinx.ext.intersphinx – Link to other projects’ documentation - Sphinx v",
                    range=types.Range(
                        start=types.Position(line=17, character=25),
                        end=types.Position(line=17, character=40),
                    ),
                ),
                types.DocumentLink(
                    target="${ROOT}/rst/roles.rst",
                    range=types.Range(
                        start=types.Position(line=28, character=34),
                        end=types.Position(line=28, character=44),
                    ),
                ),
                types.DocumentLink(
                    target="${ROOT}/myst/roles.md",
                    tooltip="Path exists",
                    range=types.Range(
                        start=types.Position(line=29, character=25),
                        end=types.Position(line=29, character=35),
                    ),
                ),
                types.DocumentLink(
                    target="https://docs.python.org/3/howto/logging.html#logging-exceptions",
                    tooltip="Exceptions raised during logging - Python v",
                    range=types.Range(
                        start=types.Position(line=30, character=49),
                        end=types.Position(line=30, character=67),
                    ),
                ),
                types.DocumentLink(
                    target="${ROOT}/myst/roles.md",
                    tooltip="Path exists",
                    range=types.Range(
                        start=types.Position(line=40, character=25),
                        end=types.Position(line=40, character=35),
                    ),
                ),
                types.DocumentLink(
                    target="${ROOT}/myst/roles.md",
                    range=types.Range(
                        start=types.Position(line=41, character=18),
                        end=types.Position(line=41, character=29),
                    ),
                ),
            ],
        ),
    ],
)
async def test_role_document_links(
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
            ["workspaces", "demo", "rst", "roles.rst"],
            # Requests for the role itself should return nothing
            types.Position(line=46, character=18),
            None,
        ),
        (
            ["workspaces", "demo", "rst", "roles.rst"],
            types.Position(line=46, character=29),
            [
                types.Location(
                    uri="${ROOT}/rst/roles.rst",
                    range=types.Range(
                        start=types.Position(line=0, character=0),
                        end=types.Position(line=1, character=0),
                    ),
                )
            ],
        ),
        (
            ["workspaces", "demo", "rst", "roles.rst"],
            types.Position(line=47, character=22),
            [
                types.Location(
                    uri="${ROOT}/myst/roles.md",
                    range=types.Range(
                        start=types.Position(line=0, character=0),
                        end=types.Position(line=1, character=0),
                    ),
                )
            ],
        ),
        (
            ["workspaces", "demo", "rst", "roles.rst"],
            types.Position(line=48, character=28),
            [
                types.Location(
                    uri="${ROOT}/myst/roles.md",
                    range=types.Range(
                        start=types.Position(line=4, character=0),
                        end=types.Position(line=5, character=0),
                    ),
                )
            ],
        ),
        (
            ["workspaces", "demo", "rst", "roles.rst"],
            types.Position(line=49, character=38),
            [
                types.Location(
                    uri="${ROOT}/rst/domains/python.rst",
                    range=types.Range(
                        start=types.Position(line=52, character=0),
                        end=types.Position(line=53, character=0),
                    ),
                )
            ],
        ),
        (
            ["workspaces", "demo", "myst", "roles.md"],
            # Requests for the role itself should return nothing
            types.Position(line=40, character=19),
            None,
        ),
        (
            ["workspaces", "demo", "myst", "roles.md"],
            types.Position(line=40, character=31),
            [
                types.Location(
                    uri="${ROOT}/myst/roles.md",
                    range=types.Range(
                        start=types.Position(line=0, character=0),
                        end=types.Position(line=1, character=0),
                    ),
                )
            ],
        ),
        (
            ["workspaces", "demo", "myst", "roles.md"],
            types.Position(line=41, character=22),
            [
                types.Location(
                    uri="${ROOT}/myst/roles.md",
                    range=types.Range(
                        start=types.Position(line=0, character=0),
                        end=types.Position(line=1, character=0),
                    ),
                )
            ],
        ),
        (
            ["workspaces", "demo", "myst", "roles.md"],
            types.Position(line=42, character=28),
            [
                types.Location(
                    uri="${ROOT}/rst/roles.rst",
                    range=types.Range(
                        start=types.Position(line=5, character=0),
                        end=types.Position(line=6, character=0),
                    ),
                )
            ],
        ),
        (
            ["workspaces", "demo", "myst", "roles.md"],
            types.Position(line=43, character=28),
            [
                types.Location(
                    uri="${ROOT}/rst/domains/python.rst",
                    range=types.Range(
                        start=types.Position(line=52, character=0),
                        end=types.Position(line=53, character=0),
                    ),
                )
            ],
        ),
    ],
)
async def test_role_target_definitions(
    client: LanguageClient,
    uri_for,
    filename: list[str],
    position: types.Position,
    expected: list[types.Location] | None,
):
    """Ensure that we handle ``textDocument/definition`` requests correctly for
    role targets."""

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


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize(
    "filename,position,expected",
    [
        (
            ["workspaces", "demo", "rst", "roles.rst"],
            # Requests for the role itself should return nothing
            types.Position(line=60, character=10),
            None,
        ),
        (
            ["workspaces", "demo", "myst", "roles.md"],
            # Requests for the role itself should return nothing
            types.Position(line=53, character=10),
            None,
        ),
        (
            ["workspaces", "demo", "rst", "roles.rst"],
            # Requests for the role itself should return nothing
            types.Position(line=60, character=26),
            types.Hover(
                contents=types.MarkupContent(
                    kind=types.MarkupKind.Markdown,
                    value="This counter implementation counts",
                ),
                range=types.Range(
                    start=types.Position(line=60, character=14),
                    end=types.Position(line=60, character=47),
                ),
            ),
        ),
        (
            ["workspaces", "demo", "myst", "roles.md"],
            # Requests for the role itself should return nothing
            types.Position(line=53, character=26),
            types.Hover(
                contents=types.MarkupContent(
                    kind=types.MarkupKind.Markdown,
                    value="This counter implementation counts",
                ),
                range=types.Range(
                    start=types.Position(line=53, character=14),
                    end=types.Position(line=53, character=47),
                ),
            ),
        ),
        (
            ["workspaces", "demo", "rst", "roles.rst"],
            # Requests for the role itself should return nothing
            types.Position(line=61, character=10),
            types.Hover(
                contents=types.MarkupContent(
                    kind=types.MarkupKind.Markdown,
                    value="Helper for creating a PatternCounter",
                ),
                range=types.Range(
                    start=types.Position(line=61, character=10),
                    end=types.Position(line=61, character=51),
                ),
            ),
        ),
        (
            ["workspaces", "demo", "myst", "roles.md"],
            # Requests for the role itself should return nothing
            types.Position(line=54, character=15),
            types.Hover(
                contents=types.MarkupContent(
                    kind=types.MarkupKind.Markdown,
                    value="Helper for creating a PatternCounter",
                ),
                range=types.Range(
                    start=types.Position(line=54, character=13),
                    end=types.Position(line=54, character=54),
                ),
            ),
        ),
        (
            ["workspaces", "demo", "rst", "roles.rst"],
            # Requests for the role itself should return nothing
            types.Position(line=62, character=43),
            types.Hover(
                contents=types.MarkupContent(
                    kind=types.MarkupKind.Markdown,
                    value="The default pattern used",
                ),
                range=types.Range(
                    start=types.Position(line=62, character=9),
                    end=types.Position(line=62, character=43),
                ),
            ),
        ),
        (
            ["workspaces", "demo", "myst", "roles.md"],
            # Requests for the role itself should return nothing
            types.Position(line=55, character=43),
            types.Hover(
                contents=types.MarkupContent(
                    kind=types.MarkupKind.Markdown,
                    value="The default pattern used",
                ),
                range=types.Range(
                    start=types.Position(line=55, character=12),
                    end=types.Position(line=55, character=46),
                ),
            ),
        ),
    ],
)
async def test_role_target_hover(
    client: LanguageClient,
    uri_for,
    filename: list[str],
    position: types.Position,
    expected: types.Hover | None,
):
    """Ensure that we handle ``textDocument/hover`` requests correctly for
    role targets."""

    root_uri = str(uri_for("workspaces", "demo"))
    test_uri = uri_for(*filename)

    fpath = pathlib.Path(test_uri)
    contents = fpath.read_text()

    # Open the file - needed so that esbonio can correctly determine the language_id of
    # the document. Strictly speaking, you could probably consider the fact that this is
    # necessary to be a bug... but 99% of the time I'm fairly sure the client will have
    # done this before making the hover call.
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

    hover = await client.text_document_hover_async(
        types.HoverParams(
            text_document=types.TextDocumentIdentifier(uri=str(test_uri)),
            position=position,
        )
    )

    if expected is None:
        assert hover is None

    else:
        assert hover.contents.value.startswith(expected.contents.value)
        assert hover.contents.kind is expected.contents.kind
        assert hover.range == expected.range
