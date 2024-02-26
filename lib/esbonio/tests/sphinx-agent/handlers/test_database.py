import pytest

from esbonio.server.features.sphinx_manager.client_subprocess import (
    SubprocessSphinxClient,
)


def anuri(base, *args):
    uri = base
    for a in args:
        uri /= a

    return str(uri.resolve())


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_files_table(client: SubprocessSphinxClient):
    """Ensure that we can correctly index all the files in the Sphinx project."""

    src = client.src_uri
    assert src is not None

    assert client.db is not None
    cursor = await client.db.execute("SELECT * FROM files")
    results = await cursor.fetchall()
    actual = {r for r in results if "badfile" not in r[1]}

    expected = {
        (anuri(src, "index.rst"), "index", "index.html"),
        (anuri(src, "rst", "directives.rst"), "rst/directives", "rst/directives.html"),
        (anuri(src, "rst", "symbols.rst"), "rst/symbols", "rst/symbols.html"),
        (
            anuri(src, "myst", "directives.md"),
            "myst/directives",
            "myst/directives.html",
        ),
        (anuri(src, "myst", "symbols.md"), "myst/symbols", "myst/symbols.html"),
        (anuri(src, "demo_rst.rst"), "demo_rst", "demo_rst.html"),
        (anuri(src, "demo_myst.md"), "demo_myst", "demo_myst.html"),
    }

    assert expected == actual
