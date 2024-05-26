from __future__ import annotations

import typing

import pytest

from esbonio.server.features.project_manager import Project

if typing.TYPE_CHECKING:
    from sphinx.application import Sphinx


@pytest.mark.asyncio
async def test_python_domain_discovery(app: Sphinx, project: Project):
    """Ensure that we can correctly index all the objects associated with the Python domain."""

    expected = set()
    domain = app.env.domains["py"]

    for name, _, objtype, docname, _, _ in domain.get_objects():
        expected.add((name, objtype, docname))

    actual = set()
    db = await project.get_db()
    cursor = await db.execute(
        "SELECT name, objtype, docname FROM objects where domain = 'py'"
    )

    for item in await cursor.fetchall():
        actual.add(item)

    assert expected == actual


@pytest.mark.asyncio
async def test_std_domain_discovery(app: Sphinx, project: Project):
    """Ensure that we can correctly index all the objects associated with the Python domain."""

    expected = set()
    domain = app.env.domains["std"]

    for name, _, objtype, docname, _, _ in domain.get_objects():
        expected.add((name, objtype, docname))

    actual = set()
    db = await project.get_db()
    cursor = await db.execute(
        "SELECT name, objtype, docname FROM objects where domain = 'std'"
    )

    for item in await cursor.fetchall():
        actual.add(item)

    assert expected == actual
