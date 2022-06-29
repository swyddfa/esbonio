import pathlib
import re
import textwrap
from typing import Iterable
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Union

import nbformat
import nbformat.v4 as nbf
from docutils import nodes
from docutils import writers
from docutils.io import StringOutput
from docutils.parsers.rst.directives.admonitions import BaseAdmonition
from sphinx.application import Sphinx
from sphinx.builders import Builder
from sphinx.util import status_iterator
from sphinx.util.docutils import new_document
from sphinx.util.logging import getLogger
from sphinx.util.osutil import copyfile
from sphinx.util.osutil import relative_uri

__version__ = "0.2.0"

logger = getLogger(__name__)
CELL_TYPES = {"markdown": nbf.new_markdown_cell, "code": nbf.new_code_cell}
REPL_PATTERN = re.compile(r"^(>>>|\.\.\.) ?", re.MULTILINE)

CODE_LANGUAGES = {"default", "python", "pycon3"}
"""The set of languages we support being exported as a notebook."""


class solution(nodes.General, nodes.Element):
    pass


def visit_solution(self, node):
    """Vistor for the HTML builder"""
    self.body.append('<details class="admonition note">\n')
    self.body.append(
        '<summary class="admonition-title"> Solution (click to reveal)</summary>\n'
    )


def depart_solution(self, node):
    """Depart-er for the HTML builder"""
    self.body.append("</details>\n")


class Solution(BaseAdmonition):

    has_content = True
    node_class = solution

    def run(self):
        (soln,) = super().run()
        return [soln]


class NotebookTranslator(nodes.NodeVisitor):
    def __init__(self, document):
        super().__init__(document)

        self.cells: List[nbformat.NotebookNode] = []
        """A list of cells that have been constructed so far."""

        self.section_level = 0
        """Used to keep track of the nested sections."""

        self._list_styles: List[str] = []
        """Used to keep track of the current list style."""

        self._prefix: List[Tuple[nodes.Node, str]] = []
        """Used to keep track of the prefix to insert before text. e.g. ``> `` for
        markdown quote blocks."""

    def asnotebook(self) -> nbformat.NotebookNode:
        # Trim any empty cells.
        cells = [c for c in self.cells if len(c.source) > 0]

        return nbf.new_notebook(cells=cells)

    def astext(self) -> str:
        return nbf.writes(self.asnotebook())

    @property
    def current_cell(self) -> Optional[nbformat.NotebookNode]:
        """Small helper for keeping track of the cell currently under construction."""

        if len(self.cells) == 0:
            return None

        return self.cells[-1]

    @property
    def list_style(self) -> str:
        """Return the current list style to use"""
        return self._list_styles[-1]

    @property
    def prefix(self) -> str:
        """Return the current prefix to insert at the start of the current line."""
        return "".join(item[1] for item in self._prefix)

    def new_cell(self, cell_type: str, *args, **kwargs) -> nbformat.NotebookNode:
        """Add a new cell to the notebook.

        To help simplify the implementation of visitors, asking for a new ``markdown`` cell
        when the current cell is also a ``markdown`` cell results in a no-op.

        Parameters
        ----------
        cell_type:
           The type of cell to create, can be either ``markdown`` or ``code``
        """

        if (
            self.current_cell is not None
            and self.current_cell.cell_type == cell_type == "markdown"
        ):
            return

        new_cell = CELL_TYPES[cell_type](*args, **kwargs)
        self.cells.append(new_cell)

        return new_cell

    def append_text(self, text: str):
        """Append text to the current cell."""

        # On the surface it would seem that doing something like
        #
        #    text = textwrap.indent(text, prefix=self.prefix)
        #
        # would be the best approach. However, it actually makes handling situations like
        # list items spanning multiple paragraphs *much* more difficult to handle.
        # By not messing with the start of the string, or the final newline, we simplify
        # the visitor code slightly.

        # If the text is just a newline on its own, include the prefix
        if text == "\n":
            self.current_cell.source += f"\n{self.prefix}"
            return

        # Remove the final newline if it exists, we'll add it back later.
        final_newline = text[-1] == "\n"
        if final_newline:
            text = text[:-1]

        text = text.replace("\n", f"\n{self.prefix}")

        if final_newline:
            text += "\n"

        self.current_cell.source += text

    def push_prefix(self, node: nodes.Node, prefix: str):
        """Push a (node, prefix) pair onto the prefix stack."""
        self._prefix.append((node, prefix))

    def pop_prefix(self, node: nodes.Node):
        """Pop the most recent element off the prefix stack, only if it corresponds to
        the given node"""

        if len(self._prefix) == 0:
            return

        if self._prefix[-1][0] == node:
            self._prefix.pop()

    # --------------------------------- Admonitions ------------------------------------

    def _visit_admonition(name):
        def visitor(self, node):
            self.new_cell("markdown")
            self.append_text(f"\n> **{name}**\n>")
            self.push_prefix(node, "> ")

        return visitor

    def _depart_admonition(self, node):
        self.pop_prefix(node)
        self.append_text("\n")

    visit_attention = _visit_admonition("Attention")
    depart_attention = _depart_admonition

    visit_caution = _visit_admonition("Caution")
    depart_caution = _depart_admonition

    visit_danger = _visit_admonition("Danger")
    depart_danger = _depart_admonition

    visit_error = _visit_admonition("Error")
    depart_error = _depart_admonition

    visit_hint = _visit_admonition("Hint")
    depart_hint = _depart_admonition

    visit_important = _visit_admonition("Important")
    depart_important = _depart_admonition

    visit_note = _visit_admonition("Note")
    depart_note = _depart_admonition

    visit_tip = _visit_admonition("Tip")
    depart_tip = _depart_admonition

    visit_warning = _visit_admonition("Warning")
    depart_warning = _depart_admonition

    # ------------------------------------ Lists ---------------------------------------

    def push_list_style(self, style: str):
        """Push a style onto the list style stack."""
        self._list_styles.append(style)

    def pop_list_style(self):
        """Pop the most recent element off the list style stack."""

        if len(self._list_styles) == 0:
            return

        self._list_styles.pop()

    def _visit_list(style: str):
        def visitor(self, node):
            self.new_cell("markdown")
            self.push_list_style(style)

        return visitor

    def _depart_list(self, node):
        self.pop_list_style()

    visit_bullet_list = _visit_list("-")
    depart_bullet_list = _depart_list

    visit_definition_list = _visit_list("-")
    depart_definition_list = _depart_list

    visit_enumerated_list = _visit_list("1.")
    depart_enumerated_list = _depart_list

    def visit_definition_list_item(self, node):
        self.append_text(f"\n{self.list_style} ")
        self.push_prefix(node, " " * (len(self.list_style) + 1))

    def depart_definition_list_item(self, node):
        self.pop_prefix(node)

    def visit_list_item(self, node):
        self.append_text(f"\n{self.list_style} ")
        self.push_prefix(node, " " * (len(self.list_style) + 1))

    def depart_list_item(self, node):
        self.pop_prefix(node)

    # ------------------------------------ Misc ----------------------------------------

    def visit_block_quote(self, node):
        self.append_text("> ")
        self.push_prefix(node, "> ")

    def depart_block_quote(self, node):
        self.pop_prefix(node)

    def visit_comment(self, node):
        node.children = []

    def visit_emphasis(self, node):
        self.append_text("*")

    def depart_emphasis(self, node):
        self.append_text("*")

    def visit_image(self, node):
        self.new_cell("markdown")
        self.append_text("![")

    def depart_image(self, node):
        self.append_text(f"]({node['uri']})")

    def visit_inline(self, node):
        self.append_text("`")

    def depart_inline(self, node):
        self.append_text("`")

    def visit_line(self, node):
        self.append_text("\n")

    def visit_line_block(self, node):
        self.append_text("\n```")

    def depart_line_block(self, node):
        self.append_text("\n```\n")

    def visit_literal(self, node):
        self.append_text("`")

    def depart_literal(self, node):
        self.append_text("`")

    def visit_literal_block(self, node):
        language = node.attributes.get("language", "none")

        if language in CODE_LANGUAGES:
            self.new_cell("code")
            return

        self.new_cell("markdown")
        self.append_text("\n```")

        if language != "none":
            self.append_text(f"{language}")

        self.append_text("\n")

    def depart_literal_block(self, node):
        language = node.attributes.get("language", "none")
        if language in CODE_LANGUAGES:
            self.new_cell("markdown")
            return

        self.append_text("\n```\n")

    def visit_math(self, node):
        self.append_text("$")

    def depart_math(self, node):
        self.append_text("$")

    def visit_paragraph(self, node):
        self.new_cell("markdown")

        # The first paragraph in a list item shouldn't insert a new line.
        if isinstance(node.parent, nodes.list_item):
            if node.parent.children.index(node) == 0:
                return

        self.append_text("\n")

    def depart_paragraph(self, node):
        self.append_text("\n")

    def visit_reference(self, node):
        # Reference nodes contain a #text node that will handle the link's label
        self.append_text("[")

    def depart_reference(self, node):
        url = node.attributes.get("refuri", None)
        anchor = node.attributes.get("refid", None)

        uri = url or anchor or "#"
        self.append_text(f"]({uri})")

    def visit_section(self, node):
        cell_id = node.attributes["ids"][0]
        self.new_cell("markdown", id=cell_id)
        self.section_level += 1

    def depart_section(self, node):
        self.section_level -= 1

    def visit_strong(self, node):
        self.append_text("**")

    def depart_strong(self, node):
        self.append_text("**")

    def visit_target(self, node):
        # Do we need to handle these at all?
        logger.debug("[tutorial]: skipping target node for now...")

    def visit_term(self, node):
        self.append_text("`")

    def depart_term(self, node):
        self.append_text("`: ")

    def visit_Text(self, node):

        if self.current_cell.cell_type == "markdown":
            self.append_text(node.astext())
            return

        # Source code blocks need special handling in that doctest blocks will be full
        # of `>>> ` or `... ` sequences which need to be removed if the code is to work
        # from within a notebook.
        source = node.astext()
        if ">>>" not in source:
            self.append_text(source)
            return

        cleaned_source = REPL_PATTERN.sub("", source)
        self.append_text(cleaned_source)

    def visit_title(self, node):
        self.append_text(f"\n{'#' * self.section_level} ")

    def depart_title(self, node):
        self.append_text("\n")

    def unknown_visit(self, node: nodes.Node) -> None:
        logger.debug(
            "[tutorial]: skipping unknown node type: '%s'", node.__class__.__name__
        )

    def unknown_departure(self, node: nodes.Node) -> None:
        pass


class NotebookWriter(writers.Writer):
    """Converts a doctree into a notebook."""

    def translate(self):
        visitor = NotebookTranslator(self.document)
        self.document.walkabout(visitor)
        self.output = visitor.astext()


class Tutorial(Builder):
    """A builder for extracting tutorials embedded in Sphinx documentation."""

    name = "tutorial"
    format = "ipynb"

    def init(self):
        self.resources = {}

        self.resource_dir = pathlib.Path(self.outdir, "resources")
        if not self.resource_dir.exists():
            self.resource_dir.mkdir(parents=True)

    def get_target_uri(self, docname: str, typ: str = None) -> str:
        return f"{docname}.ipynb"

    def get_outdated_docs(self) -> Union[str, Iterable[str]]:
        """This should return the outdated documents that should be processed.

        For the moment, we just return everything.
        """
        return self.env.found_docs

    def prepare_writing(self, docnames: Set[str]) -> None:
        pass

    def write_doc(self, docname: str, doctree: nodes.document) -> None:

        # Only process docs that have been marked as tutorials.
        metadata = self.env.metadata.get(docname)
        if metadata is None or metadata.get("tutorial", "") != "notebook":
            return

        path = pathlib.Path(docname)
        base, name = path.parent, path.stem
        outdir = pathlib.Path(self.outdir, base)

        logger.debug("[tutorial]: output directory: '%s'", outdir)
        if not outdir.exists():
            outdir.mkdir(parents=True)

        src = self.get_target_uri(docname)
        logger.debug("[tutorial]: src uri %s", src)

        self.process_images(doctree, src)
        self.process_solutions(doctree, src)

        writer = NotebookWriter()
        output = writer.write(doctree, StringOutput(encoding="utf-8"))

        outfile = outdir / f"{name}.ipynb"
        logger.debug("[tutorial]: writing notebook: '%s'", outfile)

        with outfile.open("wb") as f:
            f.write(output)

    def process_solutions(self, doctree: nodes.document, src: str) -> None:
        """Handle any solutions contained in the document.

        This ensures that a ``*.py`` file is created in the ``resources`` directory
        containing the actual solution.

        It then also rewrites the given doctree to output a pair of code cells in
        the resulting notebook. The first is a prompt for the user to input their
        solution and the second contains a :magic:`ipython:load` declaration to
        give the user the option to load in the solution if they wish to see it.

        Parameters
        ----------
        doctree:
           The doctree to process
        src:
           The path to the file containing the document being processed
        """

        docpath = pathlib.Path(src)
        logger.debug("[tutorial]: processing solutions for: %s", docpath)
        basename = f"{docpath.stem}-soln"

        for idx, soln in enumerate(doctree.traverse(condition=solution)):

            name = f"{basename}-{idx+1:02d}.py"
            destination = pathlib.Path("resources", docpath.with_suffix(""), name)
            refuri = relative_uri(src, str(destination))

            # Convert the solution to a valid Python document that can be executed.
            document = new_document("<solution>")
            document += soln

            # Rather than go through the trouble of maintaining 2 document translators,
            # one for notebooks and another for Python files. Let's just use the notebook
            # translator and do some post-processing on the result - much easier.
            translator = NotebookTranslator(document)
            document.walkabout(translator)
            notebook = translator.asnotebook()

            blocks = []
            for cell in notebook.cells:
                source = cell.source

                # Comment out the lines containing markdown.
                if cell.cell_type == "markdown":
                    source = textwrap.indent(source, "# ")

                blocks.append(source)

            self.resources[str(destination)] = ("create", "\n".join(blocks))

            # TODO: Expose config options for these
            # TODO: Translations?
            your_soln = nodes.literal_block(
                "", "# Write your solution here...\n", language="python"
            )
            load_soln = nodes.literal_block(
                "",
                f"# Execute this cell to load the example solution\n%load {refuri}\n",
                language="python",
            )

            # Replace the actual solution with the 2 cells defined above.
            soln.children = [your_soln, load_soln]

    def process_images(self, doctree: nodes.document, src: str) -> None:
        """Handle any images contained in the document.

        This ensures that the actual image files referenced by the document are copied
        to the ``resources`` folder. It also ensures that the reference to the image
        within the document is rewritten to work with the resources folder.

        Parameters
        ----------
        doctree:
           The doctree to process
        src:
           The path to the file containing the document being processed.
        """

        docpath = pathlib.Path(src)

        for image in list(doctree.traverse(condition=nodes.image)):

            source = pathlib.Path(self.app.srcdir, image["uri"])
            destination = pathlib.Path(
                "resources", docpath.with_suffix(""), source.name
            )
            refuri = relative_uri(src, str(destination))

            logger.debug("[tutorial]: image src:  %s", source)
            logger.debug("[tutorial]: image dest: %s", destination)
            logger.debug("[tutorial]: image ref:  %s", refuri)

            self.resources[str(destination)] = ("copy", source)
            image["uri"] = refuri

    def copy_resources(self):
        """Copy supporting resources to the output folder."""

        resource_iterator = status_iterator(
            self.resources.items(),
            "copying resources... ",
            "brown",
            len(self.resources),
            self.app.verbosity,
            stringify_func=lambda r: r[0],
        )

        for dest, (op, value) in resource_iterator:
            logger.debug("[tutorial]: %s: (%s, %s)", dest, op, value)

            destination = pathlib.Path(self.outdir, dest)
            if not destination.parent.exists():
                destination.parent.mkdir(parents=True)

            if op == "copy":
                copyfile(str(value), str(destination))
                continue

            if op == "create":
                with destination.open("w") as f:
                    f.write(value)

                continue

            raise TypeError(f"Unknown resource operation: '{op}'")

    def finish(self) -> None:
        self.finish_tasks.add_task(self.copy_resources)


def setup(app: Sphinx):

    app.add_node(solution, html=(visit_solution, depart_solution))

    app.add_builder(Tutorial)

    app.add_directive("solution", Solution)

    return {"version": __version__, "parallel_read_safe": True}


if __name__ == "__main__":
    import argparse
    import shutil
    import subprocess
    import sys

    import appdirs
    import pkg_resources

    cli = argparse.ArgumentParser(description="Launch the demo tutorial.")
    cli.add_argument(
        "-r",
        "--reset",
        action="store_true",
        help="reset the tutorial back to its default state.",
    )

    args = cli.parse_args()
    demo = pkg_resources.resource_filename("esbonio.tutorial", "tutorial_demo")

    source = pathlib.Path(demo)
    destination = pathlib.Path(
        appdirs.user_data_dir(appname="esbonio-tutorial", appauthor="swyddfa")
    )

    if args.reset and destination.exists():
        print(
            "Existing tutorial resources detected.",
            "This command will DELETE ALL existing files",
            "",
            sep="\n",
        )

        response = input("Do you want to continue? [y/N] ")
        if not response.lower() == "y":
            sys.exit(0)

        shutil.rmtree(destination)

    if not destination.exists():
        shutil.copytree(source, destination)

    subprocess.run(["jupyter-lab"], cwd=destination)
