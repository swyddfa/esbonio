"""An extension for helping to tailor the docs to be more relevant to the person reading.

Usage:

.. code-block:: rst

   You write your documentation as normal.
   *But* when you reach a section that only makes sense to a particular use case, etc.

   .. relevant-to:: <name>
      :category: <category>

      You include it under a ``.. relevant-to::`` directive.

   .. relevant-to:: <other-name>
      :category: <category>

      The extension will then insert a dropdown where you place a
      ``.. select-category::``, directive allowing the user to select the category that
      suits them best.

"""
import string

from docutils import nodes
from docutils.parsers.rst import Directive
from docutils.parsers.rst import directives
from docutils.transforms import Transform
from sphinx.application import Sphinx
from sphinx.util.nodes import nested_parse_with_titles


class selection(nodes.General, nodes.Element):
    ...


class script(nodes.General, nodes.Element):
    ...


class relevant_section(nodes.General, nodes.Element):
    def __repr__(self):
        return self.astext()


SELECTION_TEMPLATE = string.Template(
    """
<div class="admonition" style="font-size: var(--font-size--normal)">
 <p class="admonition-title" style="font-size: var(--font-size--normal)">
   <label>${category}</label>
   <select data-kind="relevant-to">${options}</select>
 </p>
"""
)

SCRIPT_TEMPLATE = """
<script>
    let storage = window.localStorage

    function syncDropdowns(source, others) {
        others.forEach(dropdown => {
            dropdown.selectedIndex = source.selectedIndex
            storage.setItem('selected-editor', source.selectedIndex)

            let option = dropdown.options[dropdown.selectedIndex]
            let parent = dropdown.parentElement

            if (option) {
              parent.dataset.selected = option.value
            } else {
              parent.dataset.selected = ""
            }

        })
    }

    let defaultIndex = storage.getItem('selected-editor') || 0
    let dropdowns = document.querySelectorAll('select[data-kind="relevant-to"]')
    dropdowns.forEach(d => {
        d.addEventListener('change', (evt) => syncDropdowns(evt.target, dropdowns))
    })
    dropdowns[0].selectedIndex = defaultIndex
    syncDropdowns(dropdowns[0], dropdowns)
</script>
"""


def visit_selection(self, node):
    options = []

    for value, text in node["options"]:
        options.append(f'<option value="{value}">{text}</option>')

    self.body.append(
        SELECTION_TEMPLATE.safe_substitute(
            {"category": node["category"], "options": "\n".join(options)}
        )
    )


def depart_selection(self, node):
    self.body.append("</div>")


def visit_relevant_section(self, node):
    id = node["id"]
    self.body.append(f'<div data-content="{id}">')


def depart_relevant_section(self, node):
    self.body.append("</div>")


def visit_script(self, node):
    self.body.append("<style>\n[data-content] {display: none}\n")

    for label in node["labels"]:
        self.body.append(f'[data-selected="{label}"] ~ div[data-content="{label}"] {{ ')
        self.body.append(" display: block \n}\n")

    self.body.append("</style>")
    self.body.append(SCRIPT_TEMPLATE)


def depart_script(self, node):
    ...


class Selection(Directive):
    required_arguments = 1

    def run(self):
        return []


class RelevantTo(Directive):
    required_arguments = 1
    final_argument_whitespace = True
    has_content = True

    option_spec = {"category": directives.unchanged}

    def run(self):

        section = relevant_section()
        text = self.arguments[0]

        section["text"] = text
        section["id"] = text.lower().replace(" ", "-")
        # .replace("(", "").replace(")", "")
        section["category"] = self.options.get("category", "default")

        nested_parse_with_titles(self.state, self.content, section)

        return [section]


class CollectSections(Transform):
    """Used to collect all ``relevant_section`` nodes under a common parent node
    which we can use to switch between them."""

    default_priority = 500

    def apply(self):
        sections = list(self.document.traverse(condition=relevant_section))
        if len(sections) == 0:
            return

        all_options = set()
        all_groups = []
        while len(sections) > 0:

            # Find the next common parent.
            group = selection()
            all_groups.append(group)
            parent = sections[0].parent

            start_idx = -1
            last_idx = -1

            # We'll want to modify the parent, so lets work with a copy.
            for idx, node in enumerate(list(parent.children)):
                if isinstance(node, relevant_section):

                    if start_idx < 0:
                        start_idx = idx
                        last_idx = idx
                        all_options.add((node["id"], node["text"]))

                        continue

                    # We should only collect consecutive nodes.
                    if idx - last_idx > 1:
                        break

                    last_idx = idx
                    all_options.add((node["id"], node["text"]))

            count = last_idx - start_idx
            while count >= 0:

                # Remove the node from the parent and add it to the grouping
                node = parent.children.pop(start_idx)
                assert isinstance(node, relevant_section)

                group += node
                group["category"] = node["category"]

                # Take the node out of the list to process also.
                sections.pop(0)
                count -= 1

            # Add the grouped node back into the parent.
            # group.children.sort(key=lambda n: n["id"])
            parent.children.insert(start_idx, group)

        options = sorted(list(all_options), key=lambda o: o[0])
        for group in all_groups:
            group["options"] = options

        script_ = script()
        script_["labels"] = [id_ for id_, _ in options]
        self.document += script_


def setup(app: Sphinx):

    # app.add_directive("selection", Selection)
    app.add_directive("relevant-to", RelevantTo)

    app.add_node(selection, html=(visit_selection, depart_selection))
    app.add_node(script, html=(visit_script, depart_script))
    app.add_node(
        relevant_section, html=(visit_relevant_section, depart_relevant_section)
    )

    app.add_post_transform(CollectSections)

    return {"version": "0.1.0", "parallel_read_safe": True}
