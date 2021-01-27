from mock import Mock

import py.test

from esbonio.lsp.completion.directives import DirectiveCompletion


@py.test.mark.parametrize(
    "project,expected,unexpected",
    [
        (
            "sphinx-default",
            [
                "figure",
                "function",
                "glossary",
                "image",
                "list-table",
                "module",
                "toctree",
            ],
            [
                "testcode",
                "autoclass",
                "automodule",
                "restructuredtext-test-directive",
            ],
        )
    ],
)
def test_discovery(sphinx, project, expected, unexpected):
    """Ensure that we can discover directives to offer as completion suggestions"""

    rst = Mock()
    rst.app = sphinx(project)

    completion = DirectiveCompletion(rst)
    completion.discover()

    for name in expected:
        message = "Missing directive '{}'"
        assert name in completion.directives.keys(), message.format(name)

    for name in unexpected:
        message = "Unexpected directive '{}'"
        assert name not in completion.directives.keys(), message.format(name)
