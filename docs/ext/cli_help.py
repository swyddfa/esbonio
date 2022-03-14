import importlib

from docutils import nodes
from docutils.parsers.rst import Directive
from sphinx.application import Sphinx


class CliHelp(Directive):
    required_arguments = 1
    has_content = True

    def run(self):
        name = self.arguments[0]
        mod = importlib.import_module(name)

        if not hasattr(mod, "cli"):
            return []

        cli = mod.cli
        if not hasattr(cli, "format_help"):
            return []

        return [nodes.literal_block("", cli.format_help(), language="none")]


def setup(app: Sphinx):
    app.add_directive("cli-help", CliHelp)
    return {"version": "0.1.0", "parallel_read_safe": True}
