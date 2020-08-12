import docutils.nodes as nodes
from docutils.parsers.rst.directives.admonitions import BaseAdmonition


class solution(nodes.General, nodes.Element):
    pass


class SolutionDirective(BaseAdmonition):

    has_content = True
    node_class = solution

    def run(self):
        (soln,) = super().run()
        return [soln]


def visit_solution(self, node):
    self.body.append('<details class="admonition note">\n')
    self.body.append(
        '<summary class="admonition-title"> Solution (click to reveal)</summary>\n'
    )


def depart_solution(self, node):
    self.body.append("</details>\n")


def setup(app):
    app.add_node(solution, html=(visit_solution, depart_solution))
    app.add_directive("solution", SolutionDirective)
