import itertools
import logging
import unittest.mock as mock

import py.test

from esbonio.lsp.roles import Roles
from esbonio.lsp.testing import completion_test

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

    completion_test(feature, text, expected, unexpected)


def role_target_patterns(name):
    return [
        s.format(name)
        for s in [":{}:`", ":{}:`More Info <", "   :{}:`", "   :{}:`Some Label <"]
    ]


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
                    set(),
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
                    set(),
                )
            ],
        ),
        # Python Domain
        *itertools.product(
            role_target_patterns("class"),
            [
                ("sphinx-default", {"pythagoras.Triangle"}, set()),
                ("sphinx-extensions", set(), {"pythagoras.Triangle"}),
            ],
        ),
        *itertools.product(
            role_target_patterns("py:class"),
            [
                ("sphinx-default", set(), {"pythagoras.Triangle"}),
                ("sphinx-extensions", {"pythagoras.Triangle"}, set()),
            ],
        ),
        *itertools.product(
            role_target_patterns("func"),
            [
                (
                    "sphinx-default",
                    {"pythagoras.calc_hypotenuse", "pythagoras.calc_side"},
                    set(),
                ),
                (
                    "sphinx-extensions",
                    set(),
                    {"pythagoras.calc_hypotenuse", "pythagoras.calc_side"},
                ),
            ],
        ),
        *itertools.product(
            role_target_patterns("py:func"),
            [
                (
                    "sphinx-default",
                    set(),
                    {"pythagoras.calc_hypotenuse", "pythagoras.calc_side"},
                ),
                (
                    "sphinx-extensions",
                    {"pythagoras.calc_hypotenuse", "pythagoras.calc_side"},
                    set(),
                ),
            ],
        ),
        *itertools.product(
            role_target_patterns("meth"),
            [
                ("sphinx-default", {"pythagoras.Triangle.is_right_angled"}, set()),
                ("sphinx-extensions", set(), {"pythagoras.Triangle.is_right_angled"}),
            ],
        ),
        *itertools.product(
            role_target_patterns("py:meth"),
            [
                ("sphinx-default", set(), {"pythagoras.Triangle.is_right_angled"}),
                ("sphinx-extensions", {"pythagoras.Triangle.is_right_angled"}, set()),
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
                    set(),
                ),
                (
                    "sphinx-extensions",
                    set(),
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
                    set(),
                ),
                (
                    "sphinx-default",
                    set(),
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
def test_role_target_completions(sphinx, text, setup, caplog):
    """Ensure that we can offer correct role target suggestions."""

    caplog.set_level(logging.DEBUG)
    project, expected, unexpected = setup

    rst = mock.Mock()
    rst.app = sphinx(project)
    rst.logger = logging.getLogger("rst")

    feature = Roles(rst)
    feature.initialize()

    completion_test(feature, text, expected, unexpected)
