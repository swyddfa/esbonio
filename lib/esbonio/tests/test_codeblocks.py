import itertools

import py.test

from esbonio.lsp.testing import completion_request
from esbonio.lsp.testing import directive_argument_patterns


@py.test.mark.asyncio
@py.test.mark.parametrize(
    "text,setup",
    [
        *itertools.product(
            [
                *directive_argument_patterns("code-block"),
                *directive_argument_patterns("highlight"),
            ],
            [("sphinx-default", {"console", "ng2", "python", "pycon"}, None)],
        )
    ],
)
async def test_codeblock_completions(client_server, text, setup):
    """Ensure that we can offer correct ``.. code-block::`` suggestions."""

    project, expected, unexpected = setup

    test = await client_server(project)
    test_uri = test.server.workspace.root_uri + "/test.rst"

    results = await completion_request(test, test_uri, text)

    items = {item.label for item in results.items}
    unexpected = unexpected or set()

    if expected is None:
        assert len(items) == 0
    else:
        assert expected == items & expected
        assert set() == items & unexpected
