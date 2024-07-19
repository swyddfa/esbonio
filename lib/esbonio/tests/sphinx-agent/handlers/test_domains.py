from __future__ import annotations

import typing

import pytest

from esbonio.server.features.project_manager import Project

if typing.TYPE_CHECKING:
    from typing import List

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
        "SELECT name, objtype, docname FROM objects "
        "WHERE domain = 'py' AND project IS NULL"
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
        "SELECT name, objtype, docname FROM objects "
        "WHERE domain = 'std' AND project IS NULL"
    )

    for item in await cursor.fetchall():
        actual.add(item)

    assert expected == actual


@pytest.mark.parametrize(
    "projname, domain, objtype, expected",
    [
        ("python", "py", "class", ["logging.Filter"]),
        ("sphinx", "py", "class", ["sphinx.addnodes.desc"]),
    ],
)
@pytest.mark.asyncio
async def test_intersphinx_domain_discovery(
    project: Project, domain: str, objtype: str, projname: str, expected: List[str]
):
    """Ensure that we can correctly index all the objects associated with the Python
    domain in intersphinx projects."""

    db = await project.get_db()
    cursor = await db.execute(
        "SELECT name FROM objects " "WHERE domain = ? AND objtype = ? AND project = ?",
        (domain, objtype, projname),
    )

    actual = set()
    for (name,) in await cursor.fetchall():
        actual.add(name)

    for name in expected:
        assert name in actual
