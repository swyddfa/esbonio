import itertools
import logging
import unittest.mock as mock

import py.test

from pygls.lsp.types import CompletionItemKind

from esbonio.lsp.roles import Roles
from esbonio.lsp.testing import completion_test, role_target_patterns

C_EXPECTED = {"c:func", "c:macro"}
C_UNEXPECTED = {"ref", "doc", "py:func", "py:mod"}

DEFAULT_EXPECTED = {"doc", "func", "mod", "ref", "c:func"}
DEFAULT_UNEXPECTED = {"py:func", "py:mod", "restructuredtext-unimplemented-role"}

EXT_EXPECTED = {"doc", "py:func", "py:mod", "ref", "func"}
EXT_UNEXPECTED = {"c:func", "c:macro", "restructuredtext-unimplemented-role"}

PY_EXPECTED = {"py:func", "py:mod"}
PY_UNEXPECTED = {"ref", "doc", "c:func", "c:macro"}


@py.test.mark.parametrize(
    "project,text,expected,unexpected",
    [
        ("sphinx-default", ":", DEFAULT_EXPECTED, DEFAULT_UNEXPECTED),
        ("sphinx-default", ":r", DEFAULT_EXPECTED, DEFAULT_UNEXPECTED),
        ("sphinx-default", ":ref:", None, None),
        ("sphinx-default", ":py:", None, None),
        ("sphinx-default", ":c:", C_EXPECTED, C_UNEXPECTED),
        ("sphinx-default", "some text :", DEFAULT_EXPECTED, DEFAULT_UNEXPECTED),
        ("sphinx-default", "some text :ref:", None, None),
        ("sphinx-default", "some text :py:", None, None),
        ("sphinx-default", "some text :c:", C_EXPECTED, C_UNEXPECTED),
        ("sphinx-default", "   :", DEFAULT_EXPECTED, DEFAULT_UNEXPECTED),
        ("sphinx-default", "   :r", DEFAULT_EXPECTED, DEFAULT_UNEXPECTED),
        ("sphinx-default", "   :ref:", None, None),
        ("sphinx-default", "   :py:", None, None),
        ("sphinx-default", "   :c:", C_EXPECTED, C_UNEXPECTED),
        ("sphinx-default", "   some text :", DEFAULT_EXPECTED, DEFAULT_UNEXPECTED),
        ("sphinx-default", "   some text :ref:", None, None),
        ("sphinx-default", "   some text :py:", None, None),
        ("sphinx-default", "   some text :c:", C_EXPECTED, C_UNEXPECTED),
        ("sphinx-extensions", ":", EXT_EXPECTED, EXT_UNEXPECTED),
        ("sphinx-extensions", ":r", EXT_EXPECTED, EXT_UNEXPECTED),
        ("sphinx-extensions", ":ref:", None, None),
        ("sphinx-extensions", ":py:", PY_EXPECTED, PY_UNEXPECTED),
        ("sphinx-extensions", ":c:", None, None),
        ("sphinx-extensions", "some text :", EXT_EXPECTED, EXT_UNEXPECTED),
        ("sphinx-extensions", "some text :ref:", None, None),
        ("sphinx-extensions", "some text :py:", PY_EXPECTED, PY_UNEXPECTED),
        ("sphinx-extensions", "some text :c:", None, None),
        ("sphinx-extensions", "   :", EXT_EXPECTED, EXT_UNEXPECTED),
        ("sphinx-extensions", "   :r", EXT_EXPECTED, EXT_UNEXPECTED),
        ("sphinx-extensions", "   :ref:", None, None),
        ("sphinx-extensions", "   :py:", PY_EXPECTED, PY_UNEXPECTED),
        ("sphinx-extensions", "   :c:", None, None),
        ("sphinx-extensions", "   some text :", EXT_EXPECTED, EXT_UNEXPECTED),
        ("sphinx-extensions", "   some text :ref:", None, None),
        ("sphinx-extensions", "   some text :py:", PY_EXPECTED, PY_UNEXPECTED),
        ("sphinx-extensions", "   some text :c:", None, None),
    ],
)
def test_role_completions(sphinx, project, text, expected, unexpected):
    """Ensure that we can offer correct role suggestions."""

    rst = mock.Mock()
    rst.app = sphinx(project)
    rst.logger = logging.getLogger("rst")

    feature = Roles(rst)
    feature.initialize()

    completion_test(feature, text, expected=expected, unexpected=unexpected)


@py.test.mark.parametrize(
    "text,setup",
    [
        # Standard domain
        *itertools.product(
            role_target_patterns("doc"),
            [
                (
                    "sphinx-default",
                    {"index", "glossary", "theorems/index", "theorems/pythagoras"},
                    None,
                )
            ],
        ),
        *itertools.product(
            role_target_patterns("ref"),
            [
                (
                    "sphinx-default",
                    {
                        "genindex",
                        "modindex",
                        "py-modindex",
                        "pythagoras_theorem",
                        "search",
                        "welcome",
                    },
                    None,
                )
            ],
        ),
        # Python Domain
        *itertools.product(
            role_target_patterns("class"),
            [
                ("sphinx-default", {"pythagoras.Triangle"}, None),
                ("sphinx-extensions", None, {"pythagoras.Triangle"}),
            ],
        ),
        *itertools.product(
            role_target_patterns("py:class"),
            [
                ("sphinx-default", None, {"pythagoras.Triangle"}),
                ("sphinx-extensions", {"pythagoras.Triangle"}, None),
            ],
        ),
        *itertools.product(
            role_target_patterns("func"),
            [
                (
                    "sphinx-default",
                    {"pythagoras.calc_hypotenuse", "pythagoras.calc_side"},
                    None,
                ),
                (
                    "sphinx-extensions",
                    None,
                    {"pythagoras.calc_hypotenuse", "pythagoras.calc_side"},
                ),
            ],
        ),
        *itertools.product(
            role_target_patterns("py:func"),
            [
                (
                    "sphinx-default",
                    None,
                    {"pythagoras.calc_hypotenuse", "pythagoras.calc_side"},
                ),
                (
                    "sphinx-extensions",
                    {"pythagoras.calc_hypotenuse", "pythagoras.calc_side"},
                    None,
                ),
            ],
        ),
        *itertools.product(
            role_target_patterns("meth"),
            [
                ("sphinx-default", {"pythagoras.Triangle.is_right_angled"}, None),
                ("sphinx-extensions", None, {"pythagoras.Triangle.is_right_angled"}),
            ],
        ),
        *itertools.product(
            role_target_patterns("py:meth"),
            [
                ("sphinx-default", None, {"pythagoras.Triangle.is_right_angled"}),
                ("sphinx-extensions", {"pythagoras.Triangle.is_right_angled"}, None),
            ],
        ),
        *itertools.product(
            role_target_patterns("obj"),
            [
                (
                    "sphinx-default",
                    {
                        "pythagoras",
                        "pythagoras.PI",
                        "pythagoras.UNKNOWN",
                        "pythagoras.Triangle",
                        "pythagoras.Triangle.a",
                        "pythagoras.Triangle.b",
                        "pythagoras.Triangle.c",
                        "pythagoras.Triangle.is_right_angled",
                        "pythagoras.calc_hypotenuse",
                        "pythagoras.calc_side",
                    },
                    None,
                ),
                (
                    "sphinx-extensions",
                    None,
                    {
                        "pythagoras",
                        "pythagoras.PI",
                        "pythagoras.UNKNOWN",
                        "pythagoras.Triangle",
                        "pythagoras.Triangle.a",
                        "pythagoras.Triangle.b",
                        "pythagoras.Triangle.c",
                        "pythagoras.Triangle.is_right_angled",
                        "pythagoras.calc_hypotenuse",
                        "pythagoras.calc_side",
                    },
                ),
            ],
        ),
        *itertools.product(
            role_target_patterns("py:obj"),
            [
                (
                    "sphinx-extensions",
                    {
                        "pythagoras",
                        "pythagoras.PI",
                        "pythagoras.UNKNOWN",
                        "pythagoras.Triangle",
                        "pythagoras.Triangle.a",
                        "pythagoras.Triangle.b",
                        "pythagoras.Triangle.c",
                        "pythagoras.Triangle.is_right_angled",
                        "pythagoras.calc_hypotenuse",
                        "pythagoras.calc_side",
                    },
                    None,
                ),
                (
                    "sphinx-default",
                    None,
                    {
                        "pythagoras",
                        "pythagoras.PI",
                        "pythagoras.UNKNOWN",
                        "pythagoras.Triangle",
                        "pythagoras.Triangle.a",
                        "pythagoras.Triangle.b",
                        "pythagoras.Triangle.c",
                        "pythagoras.Triangle.is_right_angled",
                        "pythagoras.calc_hypotenuse",
                        "pythagoras.calc_side",
                    },
                ),
            ],
        ),
    ],
)
def test_role_target_completions(sphinx, text, setup):
    """Ensure that we can offer correct role target suggestions."""

    project, expected, unexpected = setup

    rst = mock.Mock()
    rst.app = sphinx(project)
    rst.logger = logging.getLogger("rst")

    feature = Roles(rst)
    feature.initialize()

    completion_test(feature, text, expected=expected, unexpected=unexpected)


@py.test.mark.parametrize("obj_type", ["doc", "std:doc"])
def test_doc_target_completion_items(sphinx, obj_type):
    """Ensure that we represent ``:doc:`` completion items correctly."""

    rst = mock.Mock()
    rst.app = sphinx("sphinx-default")
    rst.logger = logging.getLogger("rst")

    roles = Roles(rst)
    item = roles.target_object_to_completion_item("index/example", "Example", obj_type)

    assert item.label == "index/example"
    assert item.kind == CompletionItemKind.File
    assert item.detail == "Example"
    assert item.insert_text == "/index/example"
