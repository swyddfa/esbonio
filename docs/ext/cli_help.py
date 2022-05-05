import argparse
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

        candidates = [
            v for v in mod.__dict__.values() if isinstance(v, argparse.ArgumentParser)
        ]
        if len(candidates) == 0:
            return []

        cli = candidates[0]
        return [nodes.literal_block("", cli.format_help(), language="none")]


def setup(app: Sphinx):
    app.add_directive("cli-help", CliHelp)
    return {"version": "0.1.0", "parallel_read_safe": True}
