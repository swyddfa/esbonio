from __future__ import annotations

import pathlib
import typing

from docutils import nodes
from docutils.transforms import Transform
from sphinx import addnodes
from sphinx import version_info

from ..log import source_to_uri_and_linum

if typing.TYPE_CHECKING:
    from typing import Dict
    from typing import Tuple

    from sphinx.application import Sphinx


STATIC_DIR = (pathlib.Path(__file__).parent.parent / "static").resolve()


def has_source(node):
    if isinstance(node, nodes.Text):
        return False

    # For some reason, including `toctreenode` causes Sphinx 5.x and 6.x to crash with a
    # cryptic error.
    #
    # AssertionError: Losing "classes" attribute
    #
    # Caused by this line:
    # https://github.com/sphinx-doc/sphinx/blob/ec993dda3690f260345133c47a4a0f6ef0b18493/sphinx/environment/__init__.py#L630
    if isinstance(node, addnodes.toctree) and version_info[0] < 7:
        return False

    return (node.line or 0) > 0 and node.source is not None


class source_locations(nodes.General, nodes.Element):
    """Index of all known source locations."""


def visit_source_locations(self, node):
    source_index: Dict[int, Tuple[str, int]] = node["index"]

    self.body.append('<div id="esbonio-marker-index" style="display: none">\n')
    for idx, (uri, linum) in source_index.items():
        self.body.append(
            f'  <span data-id="{idx}" data-uri="{uri}" data-line="{linum}"></span>\n'
        )

    self.body.append("</div>")


def depart_source_locations(self, node): ...


class SourceLocationTransform(Transform):
    """Add source location information to the doctree.

    Used to support features like synchronised scrolling.
    """

    default_priority = 500

    def apply(self, **kwargs):
        current_line = 0
        current_source = None

        source_index = {}
        source_nodes = self.document.traverse(condition=has_source)

        for idx, node in enumerate(source_nodes):
            if node.line > current_line or node.source != current_source:
                uri, linum = source_to_uri_and_linum(f"{node.source}:{node.line}")

                if uri is None or linum is None:
                    continue

                source_index[idx] = (str(uri), linum)
                node["classes"].extend(["esbonio-marker", f"esbonio-marker-{idx}"])

                # Use the source and line reported by docutils.
                # Just in case source_to_uri_and_linum doesn't handle things correctly
                current_line = node.line
                current_source = node.source

        self.document.children.append(source_locations("", index=source_index))


def setup(app: Sphinx):
    # Inline the JS code we need to enable sync scrolling.
    #
    # Yes this "bloats" every page in the generated docs, but is generally more robust
    # see: https://github.com/swyddfa/esbonio/issues/810
    webview_js = STATIC_DIR / "webview.js"
    app.add_js_file(None, body=webview_js.read_text())

    app.add_node(
        source_locations, html=(visit_source_locations, depart_source_locations)
    )
    app.add_transform(SourceLocationTransform)
