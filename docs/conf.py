# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
# -- Path setup --------------------------------------------------------------
# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
from typing import List

sys.path.insert(0, os.path.abspath("../lib/esbonio"))
sys.path.insert(0, os.path.abspath("./ext"))

from docutils.parsers.rst import nodes
from lsprotocol.types import METHOD_TO_TYPES
from lsprotocol.types import CompletionItem
from lsprotocol.types import CompletionItemKind
from sphinx.application import Sphinx

import esbonio.lsp
from esbonio.lsp.roles import Roles
from esbonio.lsp.roles import TargetCompletion
from esbonio.lsp.rst import CompletionContext

# -- Project information -----------------------------------------------------
project = "Esbonio"
copyright = "2023"
author = "the Esbonio project"
release = esbonio.lsp.__version__

DEV_BUILD = os.getenv("BUILDDIR", None) == "latest"
BRANCH = "develop" if DEV_BUILD else "release"

# -- i18n configuration ------------------------------------------------------
locale_dirs = ["locale/"]
gettext_compact = False

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_design",
    "myst_parser",
    "esbonio.relevant_to",
    "esbonio.tutorial",
    "cli_help",
    "collection_items",
    "domain",
]

autodoc_member_order = "groupwise"
autodoc_typehints = "description"
autodoc_typehints_description_target = "documented"

autodoc_pydantic_model_show_json = True

intersphinx_mapping = {
    "ipython": ("https://ipython.readthedocs.io/en/stable/", None),
    "python": ("https://docs.python.org/3/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master", None),
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "**/_*.rst", "_*.rst"]


# -- Options for HTML output -------------------------------------------------

html_theme = "furo"
html_title = "Esbonio"
html_logo = "../resources/io.github.swyddfa.Esbonio.svg"
html_favicon = "favicon.svg"
html_static_path = ["_static"]
html_theme_options = {
    "source_repository": "https://github.com/swyddfa/esbonio/",
    "source_branch": BRANCH,
    "source_directory": "docs/",
    "announcement": (
        "This is the documentation for the in-development 1.0 release of the language server. "
        '<a href="../esbonio-language-server-v0.16.4">Click here</a> to view the documentation for the current stable version'
    )
}



class LspMethod(TargetCompletion):
    """Provides completion suggestions for the custom ``:lsp:`` role."""

    def __init__(self) -> None:
        super().__init__()
        self._index_methods()

    def _index_methods(self):
        self.items = []

        for method in METHOD_TO_TYPES.keys():
            item = CompletionItem(label=method, kind=CompletionItemKind.Constant)
            self.items.append(item)

    def complete_targets(
        self, context: CompletionContext, name: str, domain: str
    ) -> List[CompletionItem]:
        if name == "lsp":
            return self.items

        return []


def lsp_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    """Link to sections within the lsp specification."""

    anchor = text.replace("/", "_")
    ref = f"https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#{anchor}"

    node = nodes.reference(rawtext, text, refuri=ref, **options)
    return [node], []


def setup(app: Sphinx):
    app.add_role("lsp", lsp_role)
    app.add_css_file("custom.css")
    app.add_object_type(
        "command", "command", objname="command", indextemplate="pair: %s; command"
    )

    app.add_object_type(
        "confval",
        "confval",
        objname="configuration value",
        indextemplate="pair: %s; configuration value",
    )

    app.add_object_type(
        "startmod",
        "startmod",
        objname="startup module",
        indextemplate="pair: %s; startup module",
    )

    app.add_object_type(
        "extmod",
        "extmod",
        objname="extension module",
        indextemplate="pair: %s; startup module",
    )

    # So that it's possible to use intersphinx to link to IPython magics
    app.add_object_type(
        "magic",
        "magic",
        objname="IPython magic",
        indextemplate="pair: %s; IPython magic",
    )


def esbonio_setup(roles: Roles):
    roles.add_target_completion_provider(LspMethod())
