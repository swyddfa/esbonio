import argparse
import json
import logging
import pathlib

import requests
from docutils import nodes
from docutils.core import publish_doctree
from docutils.core import publish_from_doctree
from docutils.nodes import NodeVisitor
from docutils.utils import new_document
from docutils.writers import Writer

logger = logging.getLogger("docgen")

DIRECTIVES_MAP = {
    "https://docutils.sourceforge.io/docs/ref/rst/directives.txt": [
        ("automatic-section-numbering", "sectnum"),
        ("attention", "-"),
        ("caution", "-"),
        ("code", "-"),
        ("compound-paragraph", "compound"),
        ("container", "-"),
        ("csv-table", "-"),
        ("danger", "-"),
        ("date", "-"),
        ("default-role", "-"),
        ("epigraph", "-"),
        ("error", "-"),
        ("figure", "-"),
        ("footer", "-"),
        ("header", "-"),
        ("highlights", "-"),
        ("generic-admonition", "admonition"),
        ("hint", "-"),
        ("image", "-"),
        ("important", "-"),
        ("include", "-"),
        ("line-block", "-"),
        ("list-table", "-"),
        ("math", "-"),
        ("metadata", "meta"),
        ("metadata-document-title", "title"),
        ("note", "-"),
        ("parsed-literal", "-"),
        ("pull-quote", "-"),
        ("raw-directive", "raw"),
        ("replace", "-"),
        ("role", "-"),
        ("rubric", "-"),
        ("sidebar", "-"),
        ("table", "-"),
        ("table-of-contents", "contents"),
        ("tip", "-"),
        ("topic", "-"),
        ("unicode", "-"),
        ("warning", "-"),
    ],
}

ROLES_MAP = {
    "https://docutils.sourceforge.io/docs/ref/rst/roles.txt": [
        ("code", "-"),
        ("emphasis", "-"),
        ("literal", "-"),
        ("math", "-"),
        ("pep-reference", "-"),
        ("raw", "-"),
        ("rfc-reference", "-"),
        ("strong", "-"),
        ("subscript", "-"),
        ("superscript", "-"),
        ("title-reference", "-"),
    ]
}


class Docutils(Writer):

    supported = ("markdown",)
    """Formats this writer supports."""

    output = None
    """Final translated form of `document`."""

    def __init__(self, url):
        super().__init__()
        self.translator_class = DocutilsTranslator
        self.url = url

    def translate(self):
        visitor = self.translator_class(self.document, self.url)
        self.document.walkabout(visitor)
        self.output = visitor.elements


class DocutilsTranslator(NodeVisitor):
    """A ``NodeVisitor`` that converts docs from ``docutils`` for an rst construct into
    a structured object the language server can use."""

    def __init__(self, document, url):
        super().__init__(document)
        self.url = url
        self.level = 1
        self.elements = {"options": {}, "body": ""}
        self.current_text = ""

    # -------------------------------- Definition Lists -------------------------------
    #
    # Typically, definition lists are used to list out the options a given construct
    # accepts. The next few methods handle the logic to manage a dictionary of options
    # and their descriptions.

    def visit_definition_list(self, node):
        self.elements["body"] += self.current_text
        self.current_text = ""

    def depart_definition_list(self, node):
        pass

    def visit_definition_list_item(self, node):
        # Get the name of the thing we're defining
        first = node.children.pop(0)

        if not isinstance(first, nodes.term):
            raise RuntimeError(f"Expected node 'term', got '{type(node)}'")

        self.key = first.astext()

        definitions = self.elements["options"]
        definitions[self.key] = {}

    def depart_definition_list_item(self, node):
        self.elements["body"] += f"\n`{self.key}`:\n" + self.current_text
        self.elements["options"][self.key] = self.current_text

        self.current_text = ""

    # -------------------------------- Field Lists ------------------------------------
    def visit_field_name(self, node):
        self.current_text += ""

    def depart_field_name(self, node):
        self.current_text += ":"

    def depart_field(self, node):
        self.current_text += "\n"

    # -------------------------------- Everything Else --------------------------------

    def depart_document(self, node):
        self.elements["body"] += self.current_text

    def visit_Text(self, node):
        self.current_text += node.astext()

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
        if not isinstance(node.parent, nodes.list_item):
            self.current_text += "\n"

    def depart_paragraph(self, node):
        self.current_text += "\n"

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


def find_section(id):
    def match_node(node):
        if not isinstance(node, nodes.section):
            return False

        return id in node["ids"]

    return match_node


def generate_documentation(mapping):
    """Generate the documentation described by the given mapping."""

    docs = {}
    for url, sections in mapping.items():
        result = requests.get(url)
        doctree = publish_doctree(source=result.text)
        maxlen = 0

        for (section, display) in sections:
            doc_id = display if display != "-" else section

            msg = f"Generating documentation: {url} - {doc_id}..."
            maxlen = max(len(msg), maxlen)
            print(msg.ljust(maxlen), end="\r")

            subtree = list(doctree.traverse(condition=find_section(section)))[0]

            document = new_document("url" + f"#{section}")
            document += subtree

            markdown = publish_from_doctree(document=document, writer=Docutils(url))
            docs[doc_id] = markdown

        msg = f"Generating documentation: {url} - done."
        maxlen = max(len(msg), maxlen)
        print(msg.ljust(maxlen))

    return docs


cli = argparse.ArgumentParser(description="generate completion item documentation.")
cli.add_argument("-o", "--output", default="docs.json", help="the file to write to")
cli.add_argument("-v", "--verbose", action="store_true", help="enable verbose output")

if __name__ == "__main__":

    args = cli.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="[%(name)s]: %(message)s")

    docs = {
        "directives": generate_documentation(DIRECTIVES_MAP),
        "roles": generate_documentation(ROLES_MAP),
    }

    with open(args.output, "w") as f:
        json.dump(docs, f, indent=2)
