from __future__ import annotations

import ast

import pytest
from lsprotocol import types

from esbonio.server.testing import range_from_str
from esbonio.sphinx_agent.app import find_extension_declaration
from esbonio.sphinx_agent.app import find_html_theme_declaration

CONF_PY = """\
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
from docutils import nodes
from sphinx.application import Sphinx

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Esbonio Demo"
copyright = "2023, Esbonio Developers"
author = "Esbonio Developers"
release = "1.0"

extensions = [ "a",
  "sphinx.ext.intersphinx",
      "myst-parser",
]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_title = "Esbonio Demo"
html_theme_options = {
    "source_repository": "https://github.com/swyddfa/esbonio",
    "source_branch": "develop",
    "source_directory": "lib/esbonio/tests/workspaces/demo/",
}
"""


@pytest.mark.parametrize(
    "src,expected",
    [
        ("", None),
        ("a=3", None),
        (CONF_PY, range_from_str("23:0-23:19")),
    ],
)
def test_find_html_theme_declaration(src: str, expected: types.Range | None):
    """Ensure that we can locate the location within a ``conf.py``
    file where the ``html_theme`` is defined."""

    mod = ast.parse(src)
    actual = find_html_theme_declaration(mod)

    if expected is None:
        assert actual is None

    else:
        assert actual.start.line == expected.start.line
        assert actual.end.line == expected.end.line

        assert actual.start.character == expected.start.character
        assert actual.end.character == expected.end.character


@pytest.mark.parametrize(
    "src,extname,expected",
    [
        ("", "myst-parser", None),
        ("a=3", "myst-parser", None),
        ("extensions='a'", "myst-parser", None),
        ("extensions=['myst-parser']", "myst-parser", range_from_str("0:12-0:25")),
        (CONF_PY, "myst-parser", range_from_str("17:6-17:19")),
    ],
)
def test_find_extension_declaration(
    src: str, extname: str, expected: types.Range | None
):
    """Ensure that we can locate the location within a ``conf.py``
    file where the ``html_theme`` is defined."""

    mod = ast.parse(src)
    actual = find_extension_declaration(mod, extname)

    if expected is None:
        assert actual is None

    else:
        assert actual.start.line == expected.start.line
        assert actual.end.line == expected.end.line

        assert actual.start.character == expected.start.character
        assert actual.end.character == expected.end.character
