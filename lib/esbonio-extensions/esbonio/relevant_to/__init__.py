import pathlib
import string

import pkg_resources
from docutils import nodes
from docutils.transforms import Transform
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective
from sphinx.util.nodes import make_id
from sphinx.util.nodes import nested_parse_with_titles


__version__ = "0.2.0"


class relevant_to_script(nodes.Element):
    """A node allowing us to inject any JS we need to make this work."""


SCRIPT = pkg_resources.resource_string("esbonio.relevant_to", "script.js").decode(
    "utf8"
)


def visit_relevant_to_script(self, node: relevant_to_script):
    # TODO: Allow this to be overidden with a local copy.
    self.body.append(
        '<script type="application/javascript" src="https://unpkg.com/htmx.org@1.7.0" integrity="sha384-EzBXYPt0/T6gxNp0nuPtLkmRpmDBbjg6WmCUZRLXBBwYYmwAUxzlSGej0ARHX0Bo" crossorigin="anonymous"></script>'
    )
    self.body.append("<script>" + SCRIPT + "</script>")


def depart_relevant_to_script(self, node: relevant_to_script):
    ...


class selection(nodes.Element):
    """A node allowing us to inject the HTML needed to swap between subjects."""


SELECTION_TEMPLATE = string.Template(
    """
<hr />
<div class="pt-2">
  <label>${category}:</label>

  <select name="subject"
          class="mb-2"
          hx-get="${docname}/:subject.html"
          hx-target="#${groupId}"
          data-category="${categoryId}"
          data-kind="relevant-to">
    ${options}
  </select>

  <div id="${groupId}">
  </div>
</div>
<hr />
"""
)


def visit_selection(self, node: selection):
    options = []
    sections = {n["id"]: n for n in node.children}

    for id_, text in sorted(node["options"], key=lambda o: o[0]):
        fragment_id = sections.get(id_, {}).get("fragment-id", "")
        options.append(f'<option data-id="{id_}" value="{fragment_id}">{text}</option>')

    self.body.append(
        SELECTION_TEMPLATE.safe_substitute(
            {
                "category": node["category"],
                "categoryId": node["category-id"],
                "docname": node["docname"],
                "options": "\n".join(options),
                "groupId": node["group-id"],
            }
        )
    )


def depart_selection(self, node: selection):
    ...


class relevant_section(nodes.Element):
    ...


def visit_relevent_section(self, node: relevant_section):
    # Swap the body out for an empty one so we can capture all the content that
    # should be written to a separate file
    node.page_body = self.body
    self.body = []


def depart_relevant_section(self, node: relevant_section):
    # Now the body contains all the content within this section, we now need to write
    # it to a file and swap the original body back in.
    fragment_id = node["fragment-id"]

    outfile = pathlib.Path(self.builder.get_target_uri(self.builder.current_docname))
    path = outfile.parent / outfile.stem / f"{fragment_id}.html"

    fragment = pathlib.Path(self.builder.outdir, path)
    if not fragment.parent.exists():
        fragment.parent.mkdir(parents=True)

    with fragment.open("w") as f:
        f.write("\n".join(self.body))

    self.body = node.page_body


class RelevantTo(SphinxDirective):
    """Used to mark sections as only relevant to certain scenarios."""

    required_arguments = 1
    final_argument_whitespace = True
    has_content = True

    def run(self):
        category = self.arguments[0]

        container = nodes.section()
        nested_parse_with_titles(self.state, self.content, container)

        sections = container[0]
        assert isinstance(sections, nodes.definition_list), "Expected definition list."

        group = selection()
        group["category"] = category
        group["category-id"] = nodes.make_id(category)
        group["docname"] = pathlib.Path(self.env.docname).parts[-1]
        group["options"] = []

        for (item, content) in sections.children:
            assert isinstance(item, nodes.term), "Expected term."
            assert isinstance(content, nodes.definition), "Expected definition"

            section = relevant_section()
            section += content.children

            section["subject"] = item.astext()
            section["id"] = nodes.make_id(section["subject"])
            section["fragment-id"] = make_id(
                self.env,
                self.state.document,
                f"{group['category-id']}-{section['id']}",
            )

            group += section
            group["options"].append((section["id"], section["subject"]))

        # Add one more section we can serve in case no subject is given in a particular
        # location.
        section = relevant_section()
        section["subject"] = "Not Found"
        section["id"] = "not-found"
        section["fragment-id"] = section["id"]
        section += nodes.paragraph("", "No content.")
        group += section

        return [group]


class CollectSections(Transform):

    default_priority = 500

    def apply(self):
        groups = list(self.document.traverse(condition=selection))
        if len(groups) == 0:
            # Nothing to do.
            return

        all_options = {}
        for group in groups:
            category = group["category"]

            for opt in group["options"]:
                all_options.setdefault(category, set()).add(opt)

        # Ensure each group presents a consistent set of options
        for idx, group in enumerate(groups):
            category = group["category"]
            group["options"] = all_options[category]
            group["group-id"] = f"group-{idx}"

        # Add the required JS to the page.
        script = relevant_to_script()
        script["options"] = all_options
        self.document += script


def setup(app: Sphinx):

    app.add_directive("relevant-to", RelevantTo)
    app.add_node(
        relevant_section, html=(visit_relevent_section, depart_relevant_section)
    )
    app.add_node(
        relevant_to_script, html=(visit_relevant_to_script, depart_relevant_to_script)
    )
    app.add_node(selection, html=(visit_selection, depart_selection))
    app.add_post_transform(CollectSections)

    return {"parallel_read_safe": True, "version": __version__}
