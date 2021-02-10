import logging
import unittest.mock as mock

import py.test

from pygls.types import CompletionItemKind

from esbonio.lsp.roles import Roles, RoleTargetCompletion
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


@py.test.mark.parametrize(
    "role,objects",
    [
        ("attr", {"attribute"}),
        ("class", {"class", "exception"}),
        ("data", {"data"}),
        ("doc", {"doc"}),
        ("envvar", {"envvar"}),
        ("exc", {"class", "exception"}),
        ("func", {"function"}),
        ("meth", {"method", "classmethod", "staticmethod"}),
        (
            "obj",
            {
                "attribute",
                "class",
                "classmethod",
                "data",
                "exception",
                "function",
                "method",
                "module",
                "staticmethod",
            },
        ),
        ("ref", {"label"}),
        ("term", {"term"}),
    ],
)
def test_target_type_discovery(sphinx, role, objects):
    """Ensure that we can correctly map roles to their correspondig object types."""

    rst = mock.Mock()
    rst.app = sphinx("sphinx-default")

    completion = RoleTargetCompletion(rst)
    completion.discover_target_types()

    assert {*completion.target_types[role]} == objects


@py.test.mark.parametrize(
    "project,type,kind,expected",
    [
        (
            "sphinx-default",
            "attribute",
            CompletionItemKind.Field,
            {"pythagoras.Triangle.a", "pythagoras.Triangle.b", "pythagoras.Triangle.c"},
        ),
        ("sphinx-default", "class", CompletionItemKind.Class, {"pythagoras.Triangle"}),
        (
            "sphinx-default",
            "doc",
            CompletionItemKind.File,
            {
                "glossary",
                "index",
                "theorems/index",
                "theorems/pythagoras",
                "directive_options",
            },
        ),
        (
            "sphinx-default",
            "envvar",
            CompletionItemKind.Variable,
            {"ANGLE_UNIT", "PRECISION"},
        ),
        (
            "sphinx-default",
            "function",
            CompletionItemKind.Function,
            {"pythagoras.calc_side", "pythagoras.calc_hypotenuse"},
        ),
        (
            "sphinx-default",
            "method",
            CompletionItemKind.Method,
            {"pythagoras.Triangle.is_right_angled"},
        ),
        ("sphinx-default", "module", CompletionItemKind.Module, {"pythagoras"}),
        (
            "sphinx-default",
            "label",
            CompletionItemKind.Reference,
            {
                "genindex",
                "modindex",
                "py-modindex",
                "pythagoras_theorem",
                "search",
                "welcome",
            },
        ),
        (
            "sphinx-default",
            "term",
            CompletionItemKind.Text,
            {"hypotenuse", "right angle"},
        ),
    ],
)
def test_target_discovery(sphinx, project, type, kind, expected):
    """Ensure that we can correctly discover role targets to suggest."""

    rst = mock.Mock()
    rst.app = sphinx(project)
    rst.app.builder.read()

    completion = RoleTargetCompletion(rst)
    completion.discover_targets()

    assert type in completion.targets
    assert expected == {item.label for item in completion.targets[type]}
    assert kind == completion.targets[type][0].kind
