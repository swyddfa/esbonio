import logging
import unittest.mock as mock

import py.test

from esbonio.lsp.directives import Directives
from esbonio.lsp.testing import completion_test


DEFAULT_EXPECTED = {
    "function",
    "module",
    "option",
    "program",
    "image",
    "toctree",
    "c:macro",
    "c:function",
}

DEFAULT_UNEXPECTED = {
    "autoclass",
    "automodule",
    "py:function",
    "py:module",
    "std:program",
    "std:option",
    "restructuredtext-test-directive",
}

EXTENSIONS_EXPECTED = {
    "autoclass",
    "automodule",
    "py:function",
    "py:module",
    "option",
    "program",
    "image",
    "toctree",
    "macro",
    "function",
}

EXTENSIONS_UNEXPECTED = {
    "c:macro",
    "module",
    "std:program",
    "std:option",
    "restructuredtext-test-directive",
}


@py.test.mark.parametrize(
    "project,text,expected,unexpected",
    [
        ("sphinx-default", ".", None, None),
        ("sphinx-default", "..", DEFAULT_EXPECTED, DEFAULT_UNEXPECTED),
        ("sphinx-default", ".. ", DEFAULT_EXPECTED, DEFAULT_UNEXPECTED),
        ("sphinx-default", ".. d", DEFAULT_EXPECTED, DEFAULT_UNEXPECTED),
        ("sphinx-default", ".. code-b", DEFAULT_EXPECTED, DEFAULT_UNEXPECTED),
        ("sphinx-default", ".. code-block::", None, None),
        ("sphinx-default", ".. py:", None, None),
        (
            "sphinx-default",
            ".. c:",
            {"c:macro", "c:function"},
            {"function", "image", "toctree"},
        ),
        ("sphinx-default", ".. _some_label:", None, None),
        ("sphinx-default", "   .", None, None),
        ("sphinx-default", "   ..", DEFAULT_EXPECTED, DEFAULT_UNEXPECTED),
        ("sphinx-default", "   .. ", DEFAULT_EXPECTED, DEFAULT_UNEXPECTED),
        ("sphinx-default", "   .. d", DEFAULT_EXPECTED, DEFAULT_UNEXPECTED),
        ("sphinx-default", "   .. doctest::", None, None),
        ("sphinx-default", "   .. code-b", DEFAULT_EXPECTED, DEFAULT_UNEXPECTED),
        ("sphinx-default", "   .. code-block::", None, None),
        ("sphinx-default", "   .. py:", None, None),
        ("sphinx-default", "   .. _some_label:", None, None),
        (
            "sphinx-default",
            "   .. c:",
            {"c:macro", "c:function"},
            {"function", "image", "toctree"},
        ),
        ("sphinx-extensions", ".", None, None),
        ("sphinx-extensions", "..", EXTENSIONS_EXPECTED, EXTENSIONS_UNEXPECTED),
        ("sphinx-extensions", ".. ", EXTENSIONS_EXPECTED, EXTENSIONS_UNEXPECTED),
        ("sphinx-extensions", ".. d", EXTENSIONS_EXPECTED, EXTENSIONS_UNEXPECTED),
        ("sphinx-extensions", ".. code-b", EXTENSIONS_EXPECTED, EXTENSIONS_UNEXPECTED),
        ("sphinx-extensions", ".. code-block::", None, None),
        ("sphinx-extensions", ".. _some_label:", None, None),
        (
            "sphinx-extensions",
            ".. py:",
            {"py:function", "py:module"},
            {"image, toctree", "macro", "function"},
        ),
        ("sphinx-extensions", ".. c:", None, None),
        ("sphinx-extensions", "   .", None, None),
        ("sphinx-extensions", "   ..", EXTENSIONS_EXPECTED, EXTENSIONS_UNEXPECTED),
        ("sphinx-extensions", "   .. ", EXTENSIONS_EXPECTED, EXTENSIONS_UNEXPECTED),
        ("sphinx-extensions", "   .. d", EXTENSIONS_EXPECTED, EXTENSIONS_UNEXPECTED),
        ("sphinx-extensions", "   .. doctest::", None, None),
        ("sphinx-extensions", "   .. _some_label:", None, None),
        (
            "sphinx-extensions",
            "   .. code-b",
            EXTENSIONS_EXPECTED,
            EXTENSIONS_UNEXPECTED,
        ),
        ("sphinx-extensions", "   .. code-block::", None, None),
        (
            "sphinx-extensions",
            ".. py:",
            {"py:function", "py:module"},
            {"image, toctree", "macro", "function"},
        ),
        ("sphinx-extensions", "   .. c:", None, None),
    ],
)
def test_directive_completions(sphinx, project, text, expected, unexpected):
    """Ensure that we can provide the correct completions for directives."""

    rst = mock.Mock()
    rst.app = sphinx(project)
    rst.logger = logging.getLogger("rst")

    feature = Directives(rst)
    feature.initialize()

    completion_test(feature, text, expected, unexpected)


AUTOCLASS_OPTS = {
    "members",
    "undoc-members",
    "noindex",
    "inherited-members",
    "show-inheritance",
    "member-order",
    "exclude-members",
    "private-members",
    "special-members",
}
IMAGE_OPTS = {"align", "alt", "class", "height", "scale", "target", "width"}
PY_FUNC_OPTS = {"annotation", "async", "module", "noindex", "noindexentry"}
C_FUNC_OPTS = {"noindexentry"}


@py.test.mark.parametrize(
    "project,text,expected,unexpected",
    [
        ("sphinx-default", ".. image:: f.png\n\f   :", IMAGE_OPTS, {"ref", "func"}),
        ("sphinx-default", ".. function:: foo\n\f   :", PY_FUNC_OPTS, {"ref", "func"}),
        (
            "sphinx-default",
            ".. autoclass:: x.y.A\n\f   :",
            set(),
            {"ref", "func"} | AUTOCLASS_OPTS,
        ),
        (
            "sphinx-default",
            "   .. image:: f.png\n\f      :",
            IMAGE_OPTS,
            {"ref", "func"},
        ),
        (
            "sphinx-default",
            "   .. function:: foo\n\f      :",
            PY_FUNC_OPTS,
            {"ref", "func"},
        ),
        (
            "sphinx-default",
            "   .. autoclass:: x.y.A\n\f      :",
            set(),
            {"ref", "func"} | AUTOCLASS_OPTS,
        ),
        ("sphinx-extensions", ".. image:: f.png\n\f   :", IMAGE_OPTS, {"ref", "func"}),
        (
            "sphinx-extensions",
            ".. function:: foo\n\f   :",
            C_FUNC_OPTS,
            {"ref", "func"},
        ),
        (
            "sphinx-extensions",
            ".. autoclass:: x.y.A\n\f   :",
            AUTOCLASS_OPTS,
            {"ref", "func"},
        ),
        (
            "sphinx-extensions",
            "   .. image:: f.png\n\f      :",
            IMAGE_OPTS,
            {"ref", "func"},
        ),
        (
            "sphinx-extensions",
            "   .. function:: foo\n\f      :",
            C_FUNC_OPTS,
            {"ref", "func"},
        ),
        (
            "sphinx-extensions",
            "   .. autoclass:: x.y.A\n\f      :",
            AUTOCLASS_OPTS,
            {"ref", "func"},
        ),
    ],
)
def test_directive_option_completions(sphinx, project, text, expected, unexpected):
    """Ensure that we can provide the correct completions for directive options."""

    rst = mock.Mock()
    rst.app = sphinx(project)
    rst.logger = logging.getLogger("rst")

    feature = Directives(rst)
    feature.initialize()

    completion_test(feature, text, expected, unexpected)
