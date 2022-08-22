"""Script to convert documentation for docutils' roles and directives into a format
the language server can use."""
import argparse
import importlib
import json
import logging
import pathlib
import sys
from urllib.request import urlopen

from docutils import nodes
from docutils.core import publish_doctree
from docutils.core import publish_from_doctree
from docutils.nodes import NodeVisitor
from docutils.parsers.rst import directives
from docutils.parsers.rst import roles
from docutils.utils import new_document
from docutils.writers import Writer

logger = logging.getLogger(__name__)


DIRECTIVES_MAPPING = {
    "automatic-section-numbering": "sectnum",
    "attention": "-",
    "caution": "-",
    "code": "-",
    "compound-paragraph": "compound",
    "container": "-",
    "csv-table": "-",
    "danger": "-",
    "date": "-",
    "default-role": "-",
    "epigraph": "-",
    "error": "-",
    "figure": "-",
    "footer": "-",
    "header": "-",
    "highlights": "-",
    "generic-admonition": "admonition",
    "hint": "-",
    "image": "-",
    "important": "-",
    "include": "-",
    "line-block": "-",
    "list-table": "-",
    "math": "-",
    "metadata": "meta",
    "metadata-document-title": "title",
    "note": "-",
    "parsed-literal": "-",
    "pull-quote": "-",
    "raw-directive": "raw",
    "replace": "-",
    "role": "-",
    "rubric": "-",
    "sidebar": "-",
    "table": "-",
    "table-of-contents": "-",
    "tip": "-",
    "topic": "-",
    "unicode": "-",
    "warning": "-",
}


ROLES_MAPPING = {
    "code": "-",
    "emphasis": "-",
    "literal": "-",
    "math": "-",
    "pep-reference": "-",
    "raw": "-",
    "rfc-reference": "-",
    "strong": "-",
    "subscript": "-",
    "superscript": "-",
    "title-reference": "-",
}


class Directive(Writer):

    supported = ("markdown",)
    output = None

    def __init__(self, url, section_url, license_url) -> None:
        super().__init__()
        self.translator_class = MarkdownTranslator
        self.url = url
        self.section_url = section_url
        self.license_url = license_url

    def translate(self):
        visitor = self.translator_class(
            self.document, self.url, self.section_url, self.license_url
        )
        self.document.walkabout(visitor)
        self.output = visitor.documentation
        self.output["description"] = self.output["description"].strip().split("\n")


class MarkdownTranslator(NodeVisitor):
    def __init__(self, document, url, section_url, license_url) -> None:
        super().__init__(document)
        self.url = url
        self.level = 1
        self.current_text = ""
        self.documentation = {
            "is_markdown": True,
            "description": "",
            "options": {},
            "source": section_url,
            "license": license_url,
        }

    def depart_document(self, node):
        self.documentation["description"] += self.current_text

    # -------------------------------- Definition Lists -------------------------------
    def visit_definition_list(self, node):
        self.documentation["description"] += self.current_text
        self.current_text = ""

    def depart_definition_list(self, node):
        pass

    def visit_definition_list_item(self, node):
        # Get the name of the thing we're defining
        first = node.children.pop(0)

        if not isinstance(first, nodes.term):
            raise RuntimeError(f"Expected node 'term', got '{type(node)}'")

        self.key = first.astext()

    def depart_definition_list_item(self, node):
        self.documentation["description"] += f"\n`{self.key}`: " + self.current_text
        self.documentation["options"][self.key] = self.current_text

        self.current_text = ""

    # -------------------------------- Field Lists ------------------------------------

    def visit_field_list(self, node):
        self.current_text += "\n| | |\n|-|-|\n"

    def visit_field_name(self, node):
        self.current_text += "| "

    def depart_field_name(self, node):
        self.current_text += " | "

    def depart_field(self, node):
        self.current_text += " |\n"

    # -------------------------------- References -------------------------------------

    def visit_reference(self, node):
        self.current_text += "["

    def depart_reference(self, node):
        uri = node.get("refuri", None)

        if not uri:
            anchor = node.get("refid", None)
            url = f"{self.url}#{anchor}"
        elif not uri.startswith("http"):
            base = pathlib.Path(self.url).parent
            url = f"{base}/{uri}"
        else:
            url = uri

        self.current_text += f"]({url})"

    # -------------------------------- Misc -------------------------------------------

    def visit_literal(self, node):
        self.current_text += "`"

    def depart_literal(self, node):
        self.current_text += "`"

    def visit_literal_block(self, node):
        self.current_text += "\n```\n"

    def depart_literal_block(self, node):
        self.current_text += "\n```\n"

    def visit_list_item(self, node):
        self.current_text += "- "

    def visit_paragraph(self, node):

        ignored_nodes = (nodes.list_item, nodes.field_body)
        if not isinstance(node.parent, ignored_nodes):
            self.current_text += "\n"

    def depart_paragraph(self, node):

        if not isinstance(node.parent, nodes.field_body):
            self.current_text += "\n"

    def visit_Text(self, node):
        self.current_text += node.astext()

    def visit_section(self, node):
        self.level += 1
        self.current_text += "\n"

    def depart_section(self, node):
        self.level -= 1
        self.current_text += "\n"

    def visit_title(self, node):
        self.current_text += "#" * self.level + " "

    def depart_title(self, node):
        self.current_text += "\n"

    def unknown_visit(self, node):
        logger.debug("skipping unknown node: '%s'", node.__class__.__name__)

    def unknown_departure(self, node):
        pass


def resolve_directive(directive):
    """Return the directive based on the given reference.

    'Core' docutils directives are returned as tuples ``(modulename, ClassName)``
    so they need to be resolved manually.
    """

    if isinstance(directive, tuple):
        mod, cls = directive

        modulename = "docutils.parsers.rst.directives.{}".format(mod)
        module = importlib.import_module(modulename)
        return getattr(module, cls)

    return directive


def find_section(id):
    def match_node(node):
        if not isinstance(node, nodes.section):
            return False

        return id in node["ids"]

    return match_node


def generate_documentation(url, mapping, items):
    docs = {}
    license_url = "https://docutils.sourceforge.io/docs/"

    with urlopen(url) as request:
        text = request.read()
        doctree = publish_doctree(source=text)

        for anchor, name in mapping.items():
            name = anchor if name == "-" else name
            item = items.get(name, None)

            subtree = list(doctree.traverse(condition=find_section(anchor)))[0]
            section_url = f"{url}#{anchor}".replace(".txt", ".html")

            document = new_document(section_url)
            document += subtree

            logger.debug("%s", publish_from_doctree(document=document).decode("utf8"))
            documentation = publish_from_doctree(
                document=document, writer=Directive(url, section_url, license_url)
            )

            if isinstance(item, tuple):
                item = resolve_directive(item)

            if item:
                try:
                    dotted_name = f"{item.__module__}.{item.__name__}"
                except AttributeError:
                    dotted_name = f"{item.__module__}.{item.__class__.__name__}"

                docs[f"{name}({dotted_name})"] = documentation

    return docs


cli = argparse.ArgumentParser(
    description="generate CompletionItem documentation for docutils roles and directives"
)
cli.add_argument(
    "-o", "--output", default=None, type=str, help="the folder to write to."
)
cli.add_argument("-v", "--verbose", action="store_true", help="enable verbose output.")


if __name__ == "__main__":
    args = cli.parse_args()

    if not args.output:
        cli.print_usage()
        sys.exit(1)

    out = pathlib.Path(args.output)
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="%(message)s")

    # Directives
    items = {
        **directives._directives,
        **directives._directive_registry,
    }

    url = "https://docutils.sourceforge.io/docs/ref/rst/directives.txt"
    filename = "directives.json"
    logger.info("Processing %s", filename)

    docs = generate_documentation(url, DIRECTIVES_MAPPING, items)

    with (out / filename).open("w") as f:
        json.dump(docs, f, indent=2)

    # Roles
    items = {
        **roles._roles,
        **roles._role_registry,
    }

    url = "https://docutils.sourceforge.io/docs/ref/rst/roles.txt"
    filename = "roles.json"
    logger.info("Processing %s", filename)

    docs = generate_documentation(url, ROLES_MAPPING, items)

    with (out / filename).open("w") as f:
        json.dump(docs, f, indent=2)
