import asyncio
import pathlib
import sys

import pytest
import pytest_lsp
from lsprotocol import types
from pytest_lsp import ClientServerConfig
from pytest_lsp import LanguageClient
from sphinx import version_info as sphinx_version

SERVER_CMD = ["-m", "esbonio"]
TEST_DIR = pathlib.Path(__file__).parent.parent


@pytest.mark.asyncio(loop_scope="session")
async def test_rst_document_diagnostic(client: LanguageClient, uri_for):
    """Ensure that we can get the diagnostics for a single rst document correctly."""

    workspace_uri = uri_for("workspaces", "demo")
    test_uri = workspace_uri / "rst" / "diagnostics.rst"
    report = await client.text_document_diagnostic_async(
        types.DocumentDiagnosticParams(
            text_document=types.TextDocumentIdentifier(uri=str(test_uri))
        )
    )

    assert report.kind == "full"

    category = " [ref.ref]" if sphinx_version[0] >= 8 else ""
    message = f"undefined label: 'not-a-real-reference'{category}"

    # We will only check the diagnostic message, full details will be handled by other
    # test cases.
    messages = {d.message for d in report.items}
    assert messages == {message}

    assert len(client.diagnostics) == 0, "Server should not publish diagnostics"


@pytest.mark.asyncio(loop_scope="session")
async def test_myst_document_diagnostic(client: LanguageClient, uri_for):
    """Ensure that we can get the diagnostics for a single myst document correctly."""

    workspace_uri = uri_for("workspaces", "demo")
    test_uri = workspace_uri / "myst" / "diagnostics.md"
    report = await client.text_document_diagnostic_async(
        types.DocumentDiagnosticParams(
            text_document=types.TextDocumentIdentifier(uri=str(test_uri))
        )
    )

    assert report.kind == "full"

    category = " [ref.ref]" if sphinx_version[0] >= 8 else ""
    message = f"undefined label: 'not-a-real-reference'{category}"

    # We will only check the diagnostic message, full details will be handled by other
    # test cases.
    messages = {d.message for d in report.items}
    assert messages == {message}

    assert len(client.diagnostics) == 0, "Server should not publish diagnostics"


@pytest.mark.asyncio(loop_scope="session")
async def test_workspace_diagnostic(client: LanguageClient, uri_for):
    """Ensure that we can get diagnostics for the whole workspace correctly."""
    report = await client.workspace_diagnostic_async(
        types.WorkspaceDiagnosticParams(previous_result_ids=[])
    )

    category = " [ref.ref]" if sphinx_version[0] >= 8 else ""
    message = f"undefined label: 'not-a-real-reference'{category}"

    workspace_uri = uri_for("workspaces", "demo")
    expected = {
        str(workspace_uri / "conf.py"): (
            "no theme named 'furo' found",
            "Could not import extension sphinx_design (exception: "
            "No module named 'sphinx_design')",
        ),
        str(workspace_uri / "index.rst"): ('Unknown directive type "grid"'),
        str(workspace_uri / "rst" / "diagnostics.rst"): (message,),
        str(workspace_uri / "myst" / "diagnostics.md"): (message,),
    }
    assert len(report.items) == len(expected)
    for item in report.items:
        for diagnostic in item.items:
            assert diagnostic.message.startswith(expected[item.uri])

    assert len(client.diagnostics) == 0, "Server should not publish diagnostics"


@pytest_lsp.fixture(
    scope="module",
    config=ClientServerConfig(
        server_command=[sys.executable, *SERVER_CMD],
    ),
)
async def pub_client(lsp_client: LanguageClient, uri_for, tmp_path_factory):
    """A client that does **not** support the pull-diagnostics model."""

    build_dir = tmp_path_factory.mktemp("build")
    workspace_uri = uri_for("workspaces", "demo")
    test_uri = workspace_uri / "rst" / "diagnostics.rst"

    await lsp_client.initialize_session(
        types.InitializeParams(
            capabilities=types.ClientCapabilities(
                # Signal workDoneProgress/create support.
                window=types.WindowClientCapabilities(
                    work_done_progress=True,
                ),
            ),
            initialization_options={
                "logging": {"level": "debug"},
                "sphinx": {
                    "buildCommand": [
                        "sphinx-build",
                        "-M",
                        "html",
                        workspace_uri.fs_path,
                        str(build_dir),
                    ],
                    "configOverrides": {
                        "html_theme": "alabaster",
                        "html_theme_options": {},
                    },
                    "pythonCommand": [sys.executable],
                },
            },
            workspace_folders=[
                types.WorkspaceFolder(uri=str(workspace_uri), name="demo"),
            ],
        )
    )

    # Open a text document to trigger sphinx client creation.
    lsp_client.text_document_did_open(
        types.DidOpenTextDocumentParams(
            text_document=types.TextDocumentItem(
                uri=str(test_uri),
                language_id="restructuredtext",
                version=0,
                text=pathlib.Path(test_uri).read_text(),
            )
        )
    )

    await lsp_client.wait_for_notification("sphinx/appCreated")

    # Save the document to trigger a build
    lsp_client.text_document_did_save(
        types.DidSaveTextDocumentParams(
            text_document=types.TextDocumentIdentifier(uri=str(test_uri))
        )
    )

    build_finished = False
    while not build_finished:
        await lsp_client.wait_for_notification("$/progress")
        report = list(lsp_client.progress_reports.values())[0][-1]
        build_finished = report.kind == "end"

    yield

    # Teardown
    await asyncio.wait_for(lsp_client.shutdown_session(), timeout=2.0)


@pytest.mark.asyncio(loop_scope="module")
async def test_publish_diagnostics(pub_client: LanguageClient, uri_for):
    """Ensure that the server publishes the diagnostics it finds"""
    workspace_uri = uri_for("workspaces", "demo")

    category = " [ref.ref]" if sphinx_version[0] >= 8 else ""
    message = f"undefined label: 'not-a-real-reference'{category}"

    expected = {
        str(workspace_uri / "rst" / "diagnostics.rst"): {message},
        str(workspace_uri / "myst" / "diagnostics.md"): {message},
    }

    # The server might not have published its diagnostics yet
    while len(pub_client.diagnostics) < len(expected):
        await pub_client.wait_for_notification(types.TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)

    for uri, expected_msgs in expected.items():
        items = pub_client.diagnostics[uri]
        actual_msgs = {d.message for d in items}

        assert expected_msgs == actual_msgs
