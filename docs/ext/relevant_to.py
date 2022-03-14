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

TODO: Allow categories to be re-used across pages
TODO: Have the JS accept a query parameter from the page's URL - makes it possible to
      link to a particular selection.
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


class relevant_to_script(nodes.General, nodes.Element):
    ...


class relevant_section(nodes.General, nodes.Element):
    def __repr__(self):
        return self.astext()


SELECTION_TEMPLATE = string.Template(
    """
<div class="admonition" style="font-size: var(--font-size--normal)">
 <p class="admonition-title" style="font-size: var(--font-size--normal)">
   <label>${category}:</label>
   <select data-category="${categoryId}" data-kind="relevant-to">${options}</select>
 </p>
"""
)

SCRIPT_TEMPLATE = """
<script>
    let storage = window.localStorage

    function syncDropdowns(source, others) {
        let category = source.dataset.category
        storage.setItem(`selected-${category}`, source.selectedIndex)

        others.forEach(dropdown => {
            dropdown.selectedIndex = source.selectedIndex


            let option = dropdown.options[dropdown.selectedIndex]
            let parent = dropdown.parentElement

            if (option) {
              parent.dataset.selected = option.value
            } else {
              parent.dataset.selected = ""
            }

        })
    }

    let dropdownMap = new Map()
    let dropdowns = document.querySelectorAll('select[data-kind="relevant-to"]')
    dropdowns.forEach(dropdown => {
        let category = dropdown.dataset.category
        if (dropdownMap.has(category)) {
            dropdownMap.get(category).push(dropdown)
        } else {
            dropdownMap.set(category, [dropdown])
        }
    })
    console.debug(dropdownMap)

    for (let [category, dropdowns] of dropdownMap.entries()) {

        dropdowns.forEach(d => {
            d.addEventListener('change', (evt) => syncDropdowns(evt.target, dropdowns))
        })

        let defaultIndex = storage.getItem(`selected-${category}`) || 0
        dropdowns[0].selectedIndex = defaultIndex
        syncDropdowns(dropdowns[0], dropdowns)
    }
</script>
"""


def visit_selection(self, node):
    options = []

    for value, text in node["options"]:
        options.append(f'<option value="{value}">{text}</option>')

    self.body.append(
        SELECTION_TEMPLATE.safe_substitute(
            {
                "category": node["category"],
                "categoryId": node["category-id"],
                "options": "\n".join(options),
            }
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

    for options in node["options"].values():
        for label, _ in options:
            self.body.append(
                f'[data-selected="{label}"] ~ div[data-content="{label}"] {{ '
            )
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

        category = self.options.get("category", "default")
        section["category"] = category
        section["category-id"] = category.lower().replace(" ", "-")

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

        all_options = {}
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
                    category = node["category"]

                    if start_idx < 0:
                        start_idx = idx
                        last_idx = idx
                        all_options.setdefault(category, set()).add(
                            (node["id"], node["text"])
                        )

                        continue

                    # We should only collect consecutive nodes.
                    if idx - last_idx > 1:
                        break

                    last_idx = idx
                    all_options.setdefault(category, set()).add(
                        (node["id"], node["text"])
                    )

            count = last_idx - start_idx
            while count >= 0:

                # Remove the node from the parent and add it to the grouping
                node = parent.children.pop(start_idx)
                assert isinstance(node, relevant_section)

                group += node
                group["category"] = node["category"]
                group["category-id"] = node["category-id"]

                # Take the node out of the list to process also.
                sections.pop(0)
                count -= 1

            # Add the grouped node back into the parent.
            # group.children.sort(key=lambda n: n["id"])
            parent.children.insert(start_idx, group)

        for group in all_groups:
            options = list(all_options[group["category"]])
            group["options"] = sorted(options, key=lambda o: o[0])

        script_ = relevant_to_script()
        script_["options"] = all_options
        self.document += script_


def setup(app: Sphinx):

    # app.add_directive("selection", Selection)
    app.add_directive("relevant-to", RelevantTo)

    app.add_node(selection, html=(visit_selection, depart_selection))
    app.add_node(relevant_to_script, html=(visit_script, depart_script))
    app.add_node(
        relevant_section, html=(visit_relevant_section, depart_relevant_section)
    )

    app.add_post_transform(CollectSections)

    return {"version": "0.1.0", "parallel_read_safe": True}
