import pathlib
import re

import docutils.nodes as nodes
import docutils.parsers.rst as rst
import nbformat.v4 as nbformat
from docutils.parsers.rst.directives.admonitions import BaseAdmonition

import esbonio

RESOURCES = "resources"


class solution(nodes.General, nodes.Element):
    pass


class SolutionDirective(BaseAdmonition):

    NAME = "solution"

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


class tutorial(nodes.General, nodes.Element):
    pass


class TutorialDirective(rst.Directive):

    NAME = "tutorial"

    def run(self):
        return [tutorial("")]


def visit_tutorial(self, node):
    pass


def depart_tutorial(self, node):
    pass


def _no_op(self, node):
    pass


no_op = _no_op, _no_op


class NotebookTranslator(nodes.NodeVisitor):
    """Walk an rst doctree and convert it into a Jupyer Notebook."""

    def __init__(self, document):
        super().__init__(document)
        self.cells = []
        self.level = 0
        self.prefix = None

    def asnotebook(self):
        return nbformat.new_notebook(cells=self.cells)

    def astext(self):
        return nbformat.writes(self.asnotebook())

    @property
    def current_cell(self):

        if len(self.cells) == 0:
            return None

        return self.cells[-1]

    def new_cell(self, cell_type: str):
        current = self.current_cell

        if current is not None and current.cell_type == cell_type == "markdown":
            return

        types = {"markdown": nbformat.new_markdown_cell, "code": nbformat.new_code_cell}
        new_cell = types[cell_type]
        self.cells.append(new_cell())

    def append(self, text: str):

        if self.prefix is not None:
            text = text.replace("\n", "\n{}".format(self.prefix))

        self.current_cell.source += text

    # --------------------------------- Visitors --------------------------------------
    visit_compound, depart_compound = no_op
    visit_compact_paragraph, depart_compact_paragraph = no_op
    visit_document, depart_document = no_op
    visit_figure, depart_figure = no_op
    visit_legend, depart_legend = no_op
    visit_solution, depart_solution = no_op
    visit_target, depart_target = no_op
    visit_tutorial, depart_tutorial = no_op

    def visit_caption(self, node):
        self.current_cell.source += "*"

    def depart_caption(self, node):
        self.current_cell.source += "*\n"

    def visit_bullet_list(self, node):
        self.new_cell("markdown")
        self.current_cell.source += "\n"

    def depart_bullet_list(self, node):
        self.current_cell.source += "\n"

    def visit_comment(self, node):
        self.new_cell("markdown")

    def depart_comment(self, node):
        pass

    def visit_emphasis(self, node):
        self.current_cell.source += "*"

    def depart_emphasis(self, node):
        self.current_cell.source += "*"

    def visit_image(self, node):
        self.new_cell("markdown")

        uri = pathlib.Path(node["uri"]).name
        fpath = pathlib.Path(RESOURCES, uri)
        self.current_cell.source += "\n![]({})\n".format(fpath)

    def depart_image(self, node):
        pass

    def visit_inline(self, node):
        self.current_cell.source += "["

    def depart_inline(self, node):
        self.current_cell.source += "]"

    def visit_list_item(self, node):
        self.append("- ")

    def depart_list_item(self, node):
        pass

    def visit_literal(self, node):
        self.current_cell.source += "`"

    def depart_literal(self, node):
        self.current_cell.source += "`"

    def visit_literal_block(self, node):
        self.new_cell("code")

    def depart_literal_block(self, node):
        pass

    def visit_note(self, node):
        self.new_cell("markdown")
        self.append("> **Note**\n")
        self.prefix = "> "

    def depart_note(self, node):
        self.prefix = None

    def visit_paragraph(self, node):
        self.new_cell("markdown")

        if isinstance(node.parent, nodes.list_item):
            return

        self.append("\n")

    def depart_paragraph(self, node):
        self.append("\n")

    def visit_reference(self, node):
        self.current_cell.source += "["

    def depart_reference(self, node):
        url = node.attributes["refuri"]
        self.current_cell.source += "]({})".format(url)

    def visit_section(self, node):
        self.level += 1
        self.new_cell("markdown")

    def depart_section(self, node):
        self.level -= 1

    def visit_strong(self, node):
        self.current_cell.source += "**"

    def depart_strong(self, node):
        self.current_cell.source += "**"

    def visit_Text(self, node):

        # Don't emit anything for rst comments.
        if isinstance(node.parent, nodes.comment):
            return

        # Nothing special to do for markdown cells.
        if self.current_cell.cell_type == "markdown":
            self.append(node.astext())
            return

        # If we're processing code, then strip any doctest markers
        pattern = re.compile("^(>>>|\\.\\.\\.) ?")
        source = "\n".join(
            [pattern.sub("", line) for line in node.astext().split("\n")]
        )
        self.append(source)

    def depart_Text(self, node):
        pass

    def visit_title(self, node):
        title = "#" * self.level
        self.append("{} ".format(title))

    def depart_title(self, node):
        self.append("\n")


def setup(app):
    app.add_node(solution, html=(visit_solution, depart_solution))
    app.add_node(tutorial, html=(visit_tutorial, depart_tutorial))

    app.add_directive(SolutionDirective.NAME, SolutionDirective)
    app.add_directive(TutorialDirective.NAME, TutorialDirective)

    return {"version": esbonio.__version__, "parallel_read_safe": True}
