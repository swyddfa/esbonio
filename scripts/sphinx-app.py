"""Script to easily get a Sphinx app to play around with.

$ python -i scripts/sphinx-app.py
Running Sphinx v4.3.0
loading intersphinx inventory from https://ipython.readthedocs.io/en/stable/objects.inv...
loading intersphinx inventory from https://docs.python.org/3/objects.inv...
loading intersphinx inventory from https://www.sphinx-doc.org/en/master/objects.inv...
building [mo]: targets for 0 po files that are out of date
building [html]: targets for 21 source files that are out of date
updating environment: [new config] 21 added, 0 changed, 0 removed
reading sources... [100%] lsp/features
looking for now-outdated files... none found
pickling environment... done
checking consistency... done
preparing documents... done
writing output... [100%] lsp/features
generating indices... genindex py-modindex done
highlighting module code... [100%] tests.test_roles
writing additional pages... search done
copying images... [100%] ../resources/images/definition-demo.gif
copying downloadable files... [100%] lsp/editors/nvim/esbonio-coc.vim
copying static files... done
copying extra files... done
dumping search index in English (code: en)... done
dumping object inventory... done
build succeeded.

The HTML pages are in docs/_build.
>>> app
<sphinx.application.Sphinx object at 0x7f0ad0fdb5b0>
"""
# ruff: noqa: F401

import inspect
import pathlib
import pdb
import time

from esbonio.sphinx_agent import types
from esbonio.sphinx_agent.app import Sphinx

try:
    root = pathlib.Path(__file__).parent.parent
    # project = root / "docs"
    project = root / "lib" / "esbonio" / "tests" / "workspaces" / "demo"
    app = Sphinx(
        srcdir=project,
        confdir=project,
        outdir=project / "_build",
        doctreedir=project / "_build" / "doctrees",
        buildername="html",
        freshenv=True,  # Have Sphinx reload everything on first build.
    )
    app.build()
except Exception:
    pdb.post_mortem()
