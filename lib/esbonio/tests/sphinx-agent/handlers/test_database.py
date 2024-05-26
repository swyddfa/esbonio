import pytest

from esbonio.server.features.project_manager import Project
from esbonio.server.features.sphinx_manager.client_subprocess import (
    SubprocessSphinxClient,
)


def anuri(base, *args):
    uri = base
    for a in args:
        uri /= a

    return str(uri.resolve())


@pytest.mark.asyncio
async def test_files_table(client: SubprocessSphinxClient, project: Project):
    """Ensure that we can correctly index all the files in the Sphinx project."""

    src = client.src_uri

    db = await project.get_db()
    cursor = await db.execute("SELECT * FROM files")
    results = await cursor.fetchall()
    actual = {r for r in results if "badfile" not in r[1]}

    expected = {
        (anuri(src, "index.rst"), "index", "index.html"),
        (anuri(src, "rst", "roles.rst"), "rst/roles", "rst/roles.html"),
        (anuri(src, "rst", "directives.rst"), "rst/directives", "rst/directives.html"),
        (
            anuri(src, "rst", "diagnostics.rst"),
            "rst/diagnostics",
            "rst/diagnostics.html",
        ),
        (
            anuri(src, "rst", "domains.rst"),
            "rst/domains",
            "rst/domains.html",
        ),
        (
            anuri(src, "rst", "domains", "python.rst"),
            "rst/domains/python",
            "rst/domains/python.html",
        ),
        (anuri(src, "rst", "symbols.rst"), "rst/symbols", "rst/symbols.html"),
        (anuri(src, "myst", "roles.md"), "myst/roles", "myst/roles.html"),
        (
            anuri(src, "myst", "directives.md"),
            "myst/directives",
            "myst/directives.html",
        ),
        (
            anuri(src, "myst", "diagnostics.md"),
            "myst/diagnostics",
            "myst/diagnostics.html",
        ),
        (anuri(src, "myst", "symbols.md"), "myst/symbols", "myst/symbols.html"),
        (anuri(src, "demo_rst.rst"), "demo_rst", "demo_rst.html"),
        (anuri(src, "demo_myst.md"), "demo_myst", "demo_myst.html"),
    }

    assert expected == actual
