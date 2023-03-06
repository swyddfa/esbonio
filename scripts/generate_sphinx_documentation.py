import argparse
import importlib
import json
import logging
import pathlib
import sys
from typing import Dict
from typing import List
from unittest import mock

import requests
import requests_cache
import sphinx.application
from docutils import nodes
from docutils.core import publish_doctree
from docutils.core import publish_from_doctree
from docutils.nodes import NodeVisitor
from docutils.parsers.rst import directives
from docutils.parsers.rst import roles
from docutils.utils import new_document
from docutils.writers import Writer
from sphinx.config import Config
from sphinx.ext.extlinks import make_link_role
from sphinx.ext.intersphinx import fetch_inventory

from esbonio.lsp.directives import DIRECTIVE
from esbonio.lsp.roles import ROLE

logger = logging.getLogger(__name__)


class MdWriter(Writer):
    supported = ("markdown",)
    output = None

    def __init__(self, url) -> None:
        super().__init__()
        self.translator_class = MarkdownTranslator
        self.url = url

    def translate(self):
        visitor = self.translator_class(self.document, self.url)
        self.document.walkabout(visitor)
        self.output = visitor.documentation
        self.output["description"] = self.output["description"].strip().split("\n")


class MarkdownTranslator(NodeVisitor):
    def __init__(self, document, url) -> None:
        super().__init__(document)
        self.url = url
        self.level = 1
        self.current_text = ""
        self.documentation = {"is_markdown": True, "description": "", "options": {}}

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


def find_section(id):
    def match_node(node):
        if not isinstance(node, nodes.section):
            return False

        return id in node["ids"]

    return match_node


def generate_documentation(mapping: Dict[str, List[Dict]], items):
    docs = {}

    for url, sections in mapping.items():
        result = requests.get(url)
        doctree = publish_doctree(source=result.text)
        # logger.debug("%s", publish_from_doctree(document=doctree).decode("utf8"))

        for section in sections:
            name = section["name"]
            anchor = section["source"].split("#")[1]

            item = items.get(name, None)
            if not item:
                logger.warning("Skipping '%s', missing implementation", name)
                continue

            subtree = list(doctree.traverse(condition=find_section(anchor)))[0]

            document = new_document(f"{url}" + f"#{anchor}")
            document += subtree

            logger.debug("%s", publish_from_doctree(document=document).decode("utf8"))
            section.update(
                publish_from_doctree(document=document, writer=MdWriter(url))
            )

            mod, impl_name = get_impl_name(item)
            dotted_name = f"{mod}.{impl_name}"
            docs[f"{name}({dotted_name})"] = section

    return docs


def mock_xref_role(original, objects_inv, *types):
    """Make custom cross-reference role implementation that appears to be the one provided."""

    mod, name = get_impl_name(original)

    logger.debug(
        "Overriding role '%s.%s' to look up object types '%s'",
        mod,
        name,
        ", ".join(types),
    )

    mock = make_xref_role(objects_inv, *types)
    mock.__module__ = mod
    mock.__name__ = name

    return mock


def make_xref_role(objects_inv, *types):
    """Return a role that looks up the correct reference from the objects.inv file."""

    def xref(role, rawtext, text, lineno, inliner, options={}, content=[]):
        match = ROLE.match(rawtext)
        logger.debug("'%s' '%s'", rawtext, match.groupdict())

        alias = match.group("alias")
        label = match.group("label")

        refuri = None
        display = alias if alias else label

        for obj in types:
            namespace = objects_inv.get(obj, {})

            if label in namespace:
                refuri = namespace[label][2]
                break

        ref = nodes.reference(text=display, refuri=refuri)
        return [ref], []

    return xref


def get_impl_name(original):
    if isinstance(original, tuple):
        return f"docutils.parsers.rst.directives.{original[0]}", original[1]

    mod = original.__module__

    try:
        name = original.__name__
    except AttributeError:
        name = original.__class__.__name__
    return mod, name


def alias_role(original, target):
    """Return a mock role implementation that behaves like ``target``"""

    mod, name = get_impl_name(original)

    def mock(*args, **kwargs):
        return target(*args, **kwargs)

    mock.__module__ = mod
    mock.__name__ = name
    return mock


def noop(self):
    """A directive implementation that does nothing."""
    return []


def insert_section(self):
    """A directive implementation that inserts its body wrapped in a section node."""
    ids = []

    if self.name == "rst:directive":
        args = [n.strip() for n in self.arguments[0].split("\n")]

        for arg in args:
            match = DIRECTIVE.match(arg)
            if match:
                name = match.group("name").replace(":", "-")
                domain = match.group("domain")

                if domain:
                    name = f"{domain}-{name}"
            else:
                name = arg

            ids.append(f"directive-{name}")

    if self.name == "rst:directive:option":
        logger.debug("%s", self.arguments)

    if self.name == "rst:role":
        args = [n.strip() for n in self.arguments[0].split("\n")]

        for arg in args:
            match = ROLE.match(arg)
            if match:
                name = match.group("name")
                domain = match.group("domain")

                if domain:
                    name = f"{domain}-{name}"
            else:
                name = arg.replace(":", "-")

            ids.append(f"role-{name}")

    section = nodes.section()
    section["ids"] = ids
    self.state.nested_parse(self.content, self.content_offset, section)

    return [section]


def mock_directives_roles(app, objects_inv):
    """xxx.

    - Ensures that all the directives and roles that Sphinx provides are registered.
    - Mocks out any implementations that assume a Sphinx environment.
    - Overrides any implementations that we need to help index/format the docs we're
      trying to create.
    """

    dirs = {**directives._directive_registry, **directives._directives}
    roles_ = roles._roles

    for name, domain in app.env.domains.items():
        logger.debug("Processing '%s' domain overrides", name)
        prefix = "" if name in {"std", "py"} else name + ":"
        target_types = {}

        for item_name, item_type in domain.object_types.items():
            for role in item_type.roles:
                key = f"{prefix}{role}"
                target_types.setdefault(key, []).append(f"{name}:{item_name}")

        # Override 'descriptive' directives to insert their content wrapped in
        # a section node.
        for directive in domain.directives:
            logger.debug("Overriding directive '%s'", key)

            key = f"{prefix}{directive}"
            impl = insert_section if dirs[key].has_content else noop
            dirs[key].run = impl

            # Needed for explicit `:py:...` references
            if domain.name == "py":
                dirs[f"{domain.name}:{directive}"].run = impl

        # Override cross-referencing role implementations to look up reference
        # from the objects.inv file we downloaded.
        for role in domain.roles:
            obj_types = target_types.get(f"{prefix}{role}", [])
            if not obj_types:
                continue

            key = f"{prefix}{role}"
            roles_[key] = mock_xref_role(roles_[key], objects_inv, *obj_types)

            # Needed for explicit `:py:...` references
            if domain.name == "py":
                roles_[f"{domain.name}:{role}"] = mock_xref_role(
                    roles_[f"{domain.name}:{role}"], objects_inv, *obj_types
                )

    dirs["codeauthor"].run = noop
    dirs["describe"].run = insert_section
    dirs["highlight"].run = noop
    dirs["index"].run = noop
    dirs["moduleauthor"].run = noop
    dirs["object"].run = insert_section
    dirs["sectionauthor"].run = noop
    dirs["versionadded"].run = insert_section
    dirs["versionchanged"].run = insert_section

    # Some roles are added as part of Sphinx's conf.py
    roles_["confval"] = make_xref_role(objects_inv, "std:confval")
    roles_["dudir"] = make_link_role(
        "dudir",
        "https://docutils.sourceforge.io/docs/ref/rst/directives.html#%s",
        "",
    )
    roles_["duref"] = make_link_role(
        "duref",
        "https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#%s",
        "",
    )

    # Override the roles that only affect formatting to fallback on something more generic.
    roles_["c:expr"] = alias_role(roles_["c:expr"], roles._role_registry["code"])
    roles_["c:texpr"] = alias_role(roles_["c:texpr"], roles._role_registry["code"])
    roles_["cpp:expr"] = alias_role(roles_["cpp:expr"], roles._role_registry["code"])
    roles_["cpp:texpr"] = alias_role(roles_["cpp:texpr"], roles._role_registry["code"])

    return dirs, {**roles._roles, **roles._role_registry}


def mock_app():
    """Create a mock Sphinx application instance."""
    app = mock.Mock()
    app.config = Config()
    app.config.intersphinx_timeout = 60

    app.env.domains = {}
    modules = list(sphinx.application.builtin_extensions)  # TODO: + sphinx.ext.zzz

    for module_name in modules:
        mod = importlib.import_module(module_name)
        mod.setup(app)

    for method_name, args, _ in app.method_calls:
        # Add any 'top-level' directives.
        if method_name == "add_directive":
            name, directive = args
            logger.debug(
                "Registering directive: '%s' '%s.%s'", name, *get_impl_name(directive)
            )

            directives.register_directive(name, directive)

        # Add any 'top-level' roles.
        if method_name == "add_role":
            name, role = args
            logger.debug("Registering role: '%s' '%s.%s'", name, *get_impl_name(role))

            roles.register_local_role(name, role)

        if method_name == "add_domain":
            domain = args[0]
            prefix = "" if domain.name in {"std", "py"} else domain.name + ":"
            app.env.domains[domain.name] = domain

            # Add any directives that have been attached to a domain.
            for name, directive in domain.directives.items():
                name = f"{prefix}{name}"
                logger.debug(
                    "Registering directive: '%s' '%s.%s'",
                    name,
                    *get_impl_name(directive),
                )

                # Needed so that explicit `.. py:...` references in the docs resolve.
                if domain.name == "py":
                    directives.register_directive(f"{domain.name}:{name}", directive)

                directives.register_directive(name, directive)

            # Add any roles that have been attached to a domain.
            for name, role in domain.roles.items():
                name = f"{prefix}{name}"
                logger.debug(
                    "Registering role: '%s' '%s.%s'", name, *get_impl_name(role)
                )

                # Needed so that explicit `:py:...` references in the docs resolve.
                if domain.name == "py":
                    roles.register_local_role(f"{domain.name}:{name}", role)

                roles.register_local_role(name, role)

    return app


def build_map(base_url, objects_inv, obj_type):
    """Build a dictionary that maps documentation sections to the object it describes.

    Parameters
    ----------
    base_url:
       The base url of the documentation site.
    objects_inv:
       The intersphinx inventory.
    obj_type:
       The object type to document.
    """
    license = "https://github.com/sphinx-doc/sphinx/blob/4.x/LICENSE"
    mapping = {}
    source_prefix = f"{base_url.rstrip('/')}/_sources/"

    for name, (_, _, url, _) in objects_inv[obj_type].items():
        source_url = (
            url.replace(base_url, source_prefix)
            .replace(".html", ".rst.txt")
            .split("#")[0]
        )

        item = {"source": url, "license": license, "name": name}
        mapping.setdefault(source_url, []).append(item)

    return mapping


cli = argparse.ArgumentParser(
    description="generate completion item documentation for sphinx roles and directives"
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
    logging.basicConfig(level=level, format="[%(levelname)s]: %(message)s")

    # Be kind and cache results while we're woking on this locally.
    requests_cache.install_cache("sphinx-doc")

    # Rather than trying to use Sphinx directly, just mock out the bare minimum.
    app = mock_app()

    # objects.inv is amazing, it's useful in so many ways! With it we can
    # - automatically discover all the (documented!) roles and directives that Sphinx provides.
    # - ensure all cross-referencing roles resolve correctly, by providing implementations that
    #   use it look up the correct url.
    # - ensure all descriptive directives produce sections with sensible ids we can use when
    #   selecting subsections of doctrees to render out.
    base_url = "https://www.sphinx-doc.org/en/master/"
    objects_inv = fetch_inventory(app, base_url, f"{base_url}objects.inv")

    # Register mocks for the additional roles and directives that Sphinx provides
    directives_, roles_ = mock_directives_roles(app, objects_inv)

    files = [
        ("directives.json", "rst:directive", directives_),
        ("roles.json", "rst:role", roles_),
    ]
    for filename, obj_type, objects in files:
        logger.info("Generating %s documentation", obj_type)

        mapping = build_map(base_url, objects_inv, obj_type)
        docs = generate_documentation(mapping, objects)

        with (out / filename).open("w") as f:
            json.dump(docs, f, indent=2)
