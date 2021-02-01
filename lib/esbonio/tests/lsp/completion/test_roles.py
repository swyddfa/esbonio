from mock import Mock

import py.test

from pygls.types import CompletionItemKind

from esbonio.lsp.completion.roles import RoleCompletion, RoleTargetCompletion


@py.test.mark.parametrize(
    "project,expected,unexpected",
    [
        (
            "sphinx-default",
            [
                "emphasis",
                "subscript",
                "raw",
                "func",
                "meth",
                "class",
                "ref",
                "doc",
                "term",
            ],
            ["named-reference", "restructuredtext-unimplemented-role"],
        )
    ],
)
def test_role_discovery(sphinx, project, expected, unexpected):
    """Ensure that we can correctly discover role definitions to offer as
    suggestions."""

    rst = Mock()
    rst.app = sphinx(project)

    completion = RoleCompletion(rst)
    completion.discover()

    for name in expected:
        message = "Missing expected role '{}'"
        assert name in completion.roles.keys(), message.format(name)

    for name in unexpected:
        message = "Unexpected role '{}'"
        assert name not in completion.roles.keys(), message.format(name)


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

    rst = Mock()
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

    rst = Mock()
    rst.app = sphinx(project)
    rst.app.builder.read()

    completion = RoleTargetCompletion(rst)
    completion.discover_targets()

    assert type in completion.targets
    assert expected == {item.label for item in completion.targets[type]}
    assert kind == completion.targets[type][0].kind
