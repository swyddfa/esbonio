import attrs
import pytest
from lsprotocol import types
from pytest_lsp import LanguageClient


@pytest.mark.asyncio
async def test_code_actions_invalid_params(client: LanguageClient):
    """Ensure that the server can handle invalid code actions data."""

    with attrs.validators.disabled():
        params = types.CodeActionParams(
            text_document=types.TextDocumentIdentifier(
                uri=client.root_uri + "/test.rst"
            ),
            range=types.Range(
                start=types.Position(line=1, character=0),
                end=types.Position(line=1, character=5),
            ),
            context=types.CodeActionContext(
                diagnostics=[
                    types.Diagnostic(
                        message="I am an invalid diagnostic",
                        range=types.Range(
                            start=types.Position(line=1, character=0),
                            end=types.Position(line=1, character=int(1e100)),
                        ),
                    )
                ]
            ),
        )

    results = await client.text_document_code_action_async(params)
    assert results == []
