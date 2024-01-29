"""A collection of items, think tabs from the sphinx-panels extension - but vertical.

Usage:

.. code-block:: rst

   .. collection:: <name>

      .. collection-item:: <item-one>

         You can include some reStructuredText here.

         .. figure:: example.png


      .. collection-item:: <item-two>

         ...

      ...
"""

import string
import uuid

from docutils import nodes
from docutils.parsers.rst import Directive
from sphinx.application import Sphinx


class collection(nodes.General, nodes.Element): ...


class collection_item(nodes.General, nodes.Element): ...


STYLE_TEMPLATE = string.Template(
    """
  input#${label}:not(:checked) ~ div[data-content="${label}"] {
    display: none;
  }

  input#${label}:not(:checked) ~ div[data-label="${label}"] {
    border-left: solid 5px #white;
  }

  input#${label}:checked ~ div[data-label="${label}"] {
    border-left: solid 5px #81d3ee;
  }
"""
)

COLLECTION_TEMPLATE = string.Template(
    """
<div class="full-width" style="display: flex">
  <div id="${id}" style="flex-shrink: 0; border-right: solid 1px #ccc; margin-right: 10px">
    ${items}
  </div>
  <div>
"""
)

COLLECTION_ITEM_LABEL_TEMPLATE = string.Template(
    """
<div data-label="${label}" style="margin-right: 5px; border-left: solid 2px white ">
  <label for="${label}" style="margin-bottom:0; margin-left: 5px">
    ${text}
  </label>
</div>
"""
)

COLLECTION_ITEM_TEMPLATE = string.Template(
    """
<input type="radio" ${checked} name="${group}" style="display: none" id="${label}" />
<div data-content="${label}">
"""
)


COLLECTION_SCRIPT_TEMPLATE = string.Template(
    """
  </div>
</div>
<script>

  function selectItem(container, target) {
    let targetId = ''

    if (target.nodeName === 'LABEL') {
      targetId = target.getAttribute('for')
    } else {
      targetId = target.getAttribute('data-label')
    }

    Array.from(container.children).forEach(item => {
      let id = item.getAttribute('data-label')

      if (targetId === id) {
        item.style.color = 'var(--color-brand-content)'
        item.style.borderColor = 'var(--color-brand-content)'
      } else {
        item.style.color = 'var(--color-content-foreground)'
        item.style.borderColor = 'var(--color-content-background)'
      }
    })
  }

  const container = document.getElementById('${id}')
  selectItem(container, container.children[0])
  container.addEventListener('click', (event) => {
    selectItem(container, event.target)
  })
</script>
"""
)


def visit_collection(self, node):
    items = []
    item_nodes = node.traverse(condition=collection_item)

    # Write out the CSS that control the selection functionality.
    self.body.append("<style>\n")

    for item in item_nodes:
        text = item["text"]
        label = item["label"]

        items.append(
            COLLECTION_ITEM_LABEL_TEMPLATE.safe_substitute(
                {"text": text, "label": label}
            )
        )

        self.body.append(STYLE_TEMPLATE.safe_substitute({"label": label}))

    self.body.append("</style>\n")
    self.body.append(
        COLLECTION_TEMPLATE.safe_substitute({"items": "".join(items), "id": node["id"]})
    )


def visit_collection_item(self, node):
    label = node["label"]
    group = node.parent["name"]
    checked = node.attributes.get("checked", None) or ""
    self.body.append(
        COLLECTION_ITEM_TEMPLATE.safe_substitute(
            {"label": label, "group": group, "checked": checked}
        )
    )


def depart_collection_item(self, node):
    self.body.append("</div>")


def depart_collection(self, node):
    self.body.append(COLLECTION_SCRIPT_TEMPLATE.safe_substitute({"id": node["id"]}))


class Collection(Directive):
    required_arguments = 1
    has_content = True

    def run(self):
        coll = collection()
        coll["id"] = str(uuid.uuid4())
        coll["name"] = self.arguments[0]
        self.state.nested_parse(self.content, self.content_offset, coll)

        items = list(coll.traverse(condition=collection_item))
        items[0]["checked"] = "checked"

        return [coll]


class CollectionItem(Directive):
    required_arguments = 1
    final_argument_whitespace = True
    has_content = True

    def run(self):
        item = collection_item()

        text = self.arguments[0]
        item["text"] = text
        item["label"] = text.lower().replace(" ", "-")

        self.state.nested_parse(self.content, self.content_offset, item)

        return [item]


def setup(app: Sphinx):
    app.add_node(collection, html=(visit_collection, depart_collection))
    app.add_node(collection_item, html=(visit_collection_item, depart_collection_item))

    app.add_directive("collection", Collection)
    app.add_directive("collection-item", CollectionItem)

    return {"version": "0.1.0", "parallel_read_safe": True}
