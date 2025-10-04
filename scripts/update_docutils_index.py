# /// script
# requires-python = ">=3.14"
# dependencies = ["docutils", "platformdirs"]
# ///
"""Script to produce an index of known role and directive implementations from
docutils.

This index contains information such as
- documentation
- known arguments/options

The output of this is NOT meant to be comprehensive, but to automate the parts that can
be automated, allowing people to focus on the last 20%.

"""

from __future__ import annotations

import argparse
import importlib
import json
import logging
import pathlib
import sys
import typing
from urllib.parse import urlparse
from urllib.request import urlopen

import platformdirs
from docutils import nodes
from docutils.core import publish_doctree, publish_from_doctree
from docutils.parsers import rst
from docutils.parsers.rst import directives, roles
from docutils.utils import new_document
from docutils.writers import Writer

if typing.TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any, TypedDict

    class RoleInfo(TypedDict):
        argument_providers: list[dict[str, Any]]

        documentation: str
        source: str
        license: str

    class DirectiveInfo(TypedDict):
        argument_providers: list[dict[str, Any]]
        option_providers: dict[str, list[dict[str, Any]] | None]

        documentation: str
        source: str
        license: str

    class DocutilsInfo(TypedDict):
        directives: dict[str, DirectiveInfo]
        roles: dict[str, RoleInfo]


DIRECTIVES_DOC_URL = "https://docutils.sourceforge.io/docs/ref/rst/directives.rst"
ROLES_DOC_URL = "https://docutils.sourceforge.io/docs/ref/rst/roles.rst"
LOG_LEVELS = [logging.WARNING, logging.INFO, logging.DEBUG]

SECTION_ID_MAP = {
    "class": "class-20",
    "contents": "table-of-contents",
    "compound": "compound-paragraph",
}


cli = argparse.ArgumentParser(
    description="update esbonio's index of docutils roles and directives"
)
cli.add_argument(
    "-o", "--output", default=None, type=str, help="the output file to write to"
)
cli.add_argument(
    "-v", "--verbose", action="count", default=0, help="enable verbose output."
)


def main(argv: Sequence[str] | None = None) -> None:
    args = cli.parse_args(argv)

    if not args.output:
        cli.print_help()
        sys.exit(1)

    logging.basicConfig(
        format="[%(levelname)s]: %(message)s",
        level=LOG_LEVELS[min(args.verbose, len(LOG_LEVELS) - 1)],
    )

    existing: DocutilsInfo
    if not (output := pathlib.Path(args.output)).exists():
        existing = {"roles": {}, "directives": {}}
    else:
        existing = json.loads(output.read_text())

    roles = update_roles(existing["roles"])
    directives = update_directives(existing["directives"])

    index = {"roles": roles, "directives": directives}
    output.write_text(json.dumps(index, indent=2) + "\n")


def update_directives(directive_index: dict[str, DirectiveInfo]):
    """Updates the existing ``directive_index`` with any new implementations/options.

    It also attempts to grab the latest documentation from the docutils documentation.
    Most importantly however, this does NOT overwrite any existing data allowing for
    additional details to be provided by hand.
    """
    items = {
        **directives._directives,  # type: ignore[attr-defined]
        **directives._directive_registry,  # type: ignore[attr-defined]
    }

    if (text := get_documentation(DIRECTIVES_DOC_URL)) is not None:
        # Hack for excluding the .. include:: ../../header2.rst directive at the top of the
        # file.
        text = text[text.find("==") :]

        # Parse the file
        doctree: nodes.document = publish_doctree(text, source_path=DIRECTIVES_DOC_URL)

        # Despite setting source_path above, the doucment source is not set...
        doctree.source = DIRECTIVES_DOC_URL.replace(".rst", ".html")

    for k, spec in items.items():
        impl, dotted_name = resolve_directive(spec)

        # Make sure we don't stomp on any existing records
        record = directive_index.setdefault(dotted_name, new_directive())
        update_documentation(record, doctree, k)

        # Ensure options are up to date
        for opt in (impl.option_spec or {}).keys():
            _ = record["option_providers"].setdefault(opt, None)

    return directive_index


def update_roles(role_index: dict[str, RoleInfo]):
    """Updates the existing ``role_index`` with any new implementations/options.

    It also attempts to grab the latest documentation from the docutils documentation.
    Most importantly however, this does NOT overwrite any existing data allowing for
    additional details to be provided by hand.
    """
    items = {
        **roles._roles,  # type: ignore[attr-defined]
        **roles._role_registry,  # type: ignore[attr-defined]
    }

    if (text := get_documentation(ROLES_DOC_URL)) is not None:
        # Hack for excluding the .. include:: ../../header2.rst directive at the top of the
        # file.
        text = text[text.find("==") :]

        # Parse the file
        doctree: nodes.document = publish_doctree(text, source_path=ROLES_DOC_URL)

        # Despite setting source_path above, the doucment source is not set...
        doctree.source = ROLES_DOC_URL.replace(".rst", ".html")

    for k, impl in items.items():
        try:
            dotted_name = f"{impl.__module__}.{impl.__name__}"
        except AttributeError:
            dotted_name = f"{impl.__module__}.{impl.__class__.__name__}"

        # Make sure we don't stomp on any existing records
        record = role_index.setdefault(dotted_name, new_role())
        update_documentation(record, doctree, k)

    return role_index


def get_documentation(url) -> str | None:
    """Fetch the documentation, from the given url.

    Cache the file locally so that we don't have to repeatedly hit the network.
    """

    result = urlparse(url)
    cache_dir = platformdirs.user_cache_path(
        appname="esbonio-dev", appauthor="swyddfa", ensure_exists=True
    )
    cache_name = cache_dir / pathlib.Path(result.path).name
    logging.debug("Cache filepath: %s", cache_name)

    if cache_name.exists():
        logging.info("Reading %s from cache", url)
        text = cache_name.read_text()
        return text

    try:
        logging.info("Reading %s from network", url)
        with urlopen(url) as request:
            text = request.read().decode()
            cache_name.write_text(text)
            return text

    except Exception:
        logging.exception(
            "Unable to fetch documentation, no documentation updates will be made"
        )
        return None


def update_documentation(
    record: DirectiveInfo | RoleInfo, doctree: nodes.document | None, item: str
):
    """Update the documentation for the given item."""
    logging.debug("Documenting item: %r", item)

    if doctree is None:
        return

    section_id = SECTION_ID_MAP.get(item, item)

    if (node := doctree.next_node(condition=find_section(section_id))) is None:
        logging.warning("Unable to find section node for %r", item)
        return

    source = doctree.source or "<document>"

    document = new_document(source)
    document += node

    record["source"] = f"{source}#{section_id}"
    record["license"] = "https://docutils.sourceforge.io/COPYING.html"
    record["documentation"] = publish_from_doctree(
        document, writer=MarkdownWriter(source)
    )


def resolve_directive(directive: tuple[str, str]) -> tuple[type[rst.Directive], str]:
    """Return the directive's implementation and 'dotted name' based on the given
    reference.

    'Core' docutils directives are returned as tuples ``(modulename, ClassName)``
    so they need to imported manually.
    """
    mod, cls = directive

    modulename = "docutils.parsers.rst.directives.{}".format(mod)
    module = importlib.import_module(modulename)
    impl: type[rst.Directive] = getattr(module, cls)

    try:
        dotted_name = f"{impl.__module__}.{impl.__name__}"
    except AttributeError:
        dotted_name = f"{impl.__module__}.{impl.__class__.__name__}"

    return impl, dotted_name


def new_directive() -> DirectiveInfo:
    """Return a new directive record."""
    return {
        "documentation": "",
        "option_providers": {},
        "argument_providers": [],
        "source": "",
        "license": "",
    }


def new_role() -> RoleInfo:
    """Return a new role record."""
    return {
        "documentation": "",
        "argument_providers": [],
        "source": "",
        "license": "",
    }


def find_section(id: str):
    """Return a function that selects a section in a doctree based on the given od."""

    def match_node(node: nodes.Node):
        if not isinstance(node, nodes.section):
            return False

        return id in node["ids"]

    return match_node


class MarkdownWriter(Writer):
    supported = ("markdown",)

    def __init__(self, url: str) -> None:
        super().__init__()
        self.translator_class = MarkdownTranslator
        self.url = url

    def translate(self):
        visitor = self.translator_class(self.document, self.url)
        self.document.walkabout(visitor)
        self.output = visitor.lines


@typing.final
class MarkdownTranslator(nodes.NodeVisitor):
    """Walk a doctree converting it to markdown."""

    def __init__(self, document: nodes.document, url: str) -> None:
        super().__init__(document)
        self.level = 0
        self.current_text = ""
        self.lines: list[str] = []
        self.url = url

    def commit_text(self):
        self.lines.extend(self.current_text.split("\n"))
        self.current_text = ""

    def astext(self):
        return "\n".join(self.lines)

    @typing.override
    def visit_document(self, node: nodes.document):
        pass

    @typing.override
    def depart_document(self, node: nodes.document):
        pass

    @typing.override
    def visit_section(self, node: nodes.section):
        self.level += 1

    @typing.override
    def depart_section(self, node: nodes.section):
        self.level -= 1

    @typing.override
    def visit_title(self, node: nodes.title):
        if isinstance(node.parent, nodes.section):
            self.current_text += f"{'#' * self.level} "

        elif isinstance(node.parent, (nodes.admonition, nodes.topic)):
            pass

        else:
            logging.warning("title node in unknown context: %r", node.parent)

    @typing.override
    def visit_paragraph(self, node: nodes.paragraph):
        ignored_nodes = (nodes.list_item, nodes.field_body)
        if not isinstance(node.parent, ignored_nodes):
            self.commit_text()

    @typing.override
    def depart_paragraph(self, node: nodes.paragraph):
        if not isinstance(node.parent, nodes.field_body):
            self.commit_text()

    # -------------------------------- Admonitions-------------------------------------

    @typing.override
    def visit_admonition(self, node: nodes.admonition):
        if (title_node := node.next_node(nodes.title)) is not None:
            title = title_node.astext()
        else:
            title = "Admonition"

        self._admonition_visit(title)

    @typing.override
    def depart_admonition(self, node: nodes.admonition):
        self._admonition_depart()

    @typing.override
    def visit_block_quote(self, node: nodes.block_quote):
        self._admonition_visit("")

    @typing.override
    def depart_block_quote(self, node: nodes.block_quote):
        self._admonition_depart()

    @typing.override
    def visit_caution(self, node: nodes.caution):
        self._admonition_visit("caution")

    @typing.override
    def depart_caution(self, node: nodes.caution):
        self._admonition_depart()

    @typing.override
    def visit_note(self, node: nodes.note):
        self._admonition_visit("note")

    @typing.override
    def depart_note(self, node: nodes.note):
        self._admonition_depart()

    @typing.override
    def visit_tip(self, node: nodes.tip):
        self._admonition_visit("tip")

    @typing.override
    def depart_tip(self, node: nodes.tip):
        self._admonition_depart()

    @typing.override
    def visit_topic(self, node: nodes.topic):
        if (title_node := node.next_node(nodes.title)) is not None:
            node.children.remove(title_node)
            title = title_node.astext()
        else:
            title = "Topic"

        self._admonition_visit(title)

    @typing.override
    def depart_topic(self, node: nodes.topic):
        self._admonition_depart()

    @typing.override
    def visit_warning(self, node: nodes.warning):
        self._admonition_visit("warning")

    @typing.override
    def depart_warning(self, node: nodes.warning):
        self._admonition_depart()

    def _admonition_visit(self, name: str):
        self.commit_text()
        title = f"**{name.upper()}**" if len(name) > 0 else ""
        self.current_text = f"----\n{title}\n"
        self.commit_text()

    def _admonition_depart(self):
        self.commit_text()
        self.current_text = "----"
        self.commit_text()

    # -------------------------------- References -------------------------------------

    @typing.override
    def visit_reference(self, node: nodes.reference):
        self.current_text += "["

    @typing.override
    def depart_reference(self, node: nodes.reference):
        uri = node.get("refuri", None)

        if not uri:
            anchor = node.get("refid", None)
            url = f"{self.url}#{anchor}"
        elif not uri.startswith("http"):
            base = pathlib.Path(self.url).parent
            url = f"{base}/{uri}"
        else:
            url = uri

        # Fix https:/docutils...
        if url.startswith("https:/") and not url.startswith("https://"):
            url = url.replace("https:/", "https://")

        self.current_text += f"]({url})"

    @typing.override
    def visit_target(self, node: nodes.target):
        pass

    @typing.override
    def visit_substitution_definition(self, node: nodes.substitution_definition):
        pass

    # -------------------------------- Bullet Lists -----------------------------------

    @typing.override
    def visit_bullet_list(self, node: nodes.bullet_list):
        pass

    @typing.override
    def visit_list_item(self, node: nodes.list_item):
        self.current_text += "- "

    # -------------------------------- Definition Lists -------------------------------

    @typing.override
    def visit_definition_list(self, node: nodes.definition_list):
        self.commit_text()

    @typing.override
    def depart_definition_list(self, node: nodes.definition_list):
        pass

    @typing.override
    def visit_definition_list_item(self, node: nodes.definition_list_item):
        # Get the name of the thing we're defining
        first = node.children.pop(0)

        if not isinstance(first, nodes.term):
            raise RuntimeError(f"Expected node 'term', got '{type(node)}'")

        self.key = first.astext()
        self.current_text += f"`{self.key}`: "

    @typing.override
    def depart_definition_list_item(self, node: nodes.definition_list_item):
        self.commit_text()

    @typing.override
    def visit_definition(self, node: nodes.definition):
        pass

    @typing.override
    def visit_classifier(self, node: nodes.classifier):
        pass

    @typing.override
    def depart_classifier(self, node: nodes.classifier):
        self.commit_text()

    # -------------------------------- Field Lists ------------------------------------

    @typing.override
    def visit_field_list(self, node: nodes.field_list):
        self.current_text += "\n| | |\n|-|-|"
        self.commit_text()

    @typing.override
    def visit_field_name(self, node: nodes.field_name):
        self.current_text += "| "

    @typing.override
    def depart_field_name(self, node: nodes.field_name):
        self.current_text += " | "

    @typing.override
    def visit_field(self, node: nodes.field):
        pass

    @typing.override
    def depart_field(self, node: nodes.field):
        self.current_text += " |"
        self.commit_text()

    @typing.override
    def visit_field_body(self, node: nodes.field_body):
        pass

    @typing.override
    def depart_field_body(self, node: nodes.field_body):
        self.current_text = self.current_text.replace("\n", "")
        pass

    # --------------------------------- Footnotes -------------------------------------

    @typing.override
    def visit_footnote_reference(self, node: nodes.footnote_reference):
        self.current_text += "[^"

    @typing.override
    def depart_footnote_reference(self, node: nodes.footnote_reference):
        self.current_text += "]"

    @typing.override
    def visit_footnote(self, node: nodes.footnote):
        pass

    @typing.override
    def depart_footnote(self, node: nodes.footnote):
        self.commit_text()

    @typing.override
    def visit_label(self, node: nodes.label):
        self.current_text += "[^"

    @typing.override
    def depart_label(self, node: nodes.label):
        self.current_text += "]: "

    # --------------------------------- Misc ------------------------------------------

    @typing.override
    def visit_attribution(self, node: nodes.attribution):
        self.commit_text()
        self.current_text = "-- "

    @typing.override
    def depart_attribution(self, node: nodes.attribution):
        self.commit_text()

    @typing.override
    def visit_comment(self, node: nodes.comment):
        node.children = []

    @typing.override
    def visit_literal(self, node: nodes.literal):
        self.current_text += "`"

    @typing.override
    def depart_literal(self, node: nodes.literal):
        self.current_text += "`"

    @typing.override
    def visit_literal_block(self, node: nodes.literal_block):
        self.lines.append("```")

    @typing.override
    def depart_literal_block(self, node: nodes.literal_block):
        self.commit_text()
        self.lines.append("```")

    @typing.override
    def visit_strong(self, node: nodes.strong):
        self.current_text += "**"

    @typing.override
    def depart_strong(self, node: nodes.strong):
        self.current_text += "**"

    @typing.override
    def visit_emphasis(self, node: nodes.emphasis):
        self.current_text += "*"

    @typing.override
    def depart_emphasis(self, node: nodes.emphasis):
        self.current_text += "*"

    @typing.override
    def visit_Text(self, node: nodes.Text):
        if isinstance(node.parent, nodes.substitution_definition):
            return

        self.current_text += node.astext()

    @typing.override
    def unknown_visit(self, node):
        logging.warning("skipping unknown node: '%s'", node.__class__.__name__)

    @typing.override
    def unknown_departure(self, node):
        pass


if __name__ == "__main__":
    main()
