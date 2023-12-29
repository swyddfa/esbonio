import pathlib

import pytest
from pygls import IS_WIN

from esbonio.server.features.sphinx_manager.client_subprocess import (
    SubprocessSphinxClient,
)


def apath(*args):
    p = str(pathlib.Path(*args).resolve())

    if IS_WIN:
        return p.lower()

    return p


@pytest.mark.asyncio
async def test_files_table(client: SubprocessSphinxClient):
    """Ensure that we can correctly index all the files in the Sphinx project."""

    src = client.src_uri
    assert src is not None

    assert client.db is not None
    cursor = await client.db.execute("SELECT * FROM files")
    results = await cursor.fetchall()

    if IS_WIN:
        # Paths are case insensitive on Windows
        actual = {(p.lower(), d, u) for (p, d, u) in results if "badfile" not in d}
    else:
        actual = {r for r in results if "badfile" not in r[1]}

    expected = {
        # Ignore this file..., it's behavior seems very inconsistent across
        # Python/Sphinx versions...
        # (apath(src, "..", "badfile.rst"), "../badfile", "definitions.html"),
        (apath(src, "index.rst"), "index", "index.html"),
    }

    assert expected == actual
