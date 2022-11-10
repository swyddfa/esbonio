"""CustomHTMLTranslator class."""
from typing import List

from docutils.nodes import Node
from sphinx.writers.html import HTMLTranslator


class CustomHTMLTranslator(HTMLTranslator):  # pylint: disable=abstract-method
    """Custom HTMLTranslator extending the sphinx HTMLTranslator for our needs.

    Additional logic for
    - progress report
    - adding linemarkers for scroll-sync
    are added to the original dispatch_visit method.
    """

    recent_nodesource: str = ""
    docnames: List[str] = []
    doccount: int = 0
    progress: float = 0

    def __init__(self, builder, *args, **kwds):
        # HTMLTranslator is an old-style Python class, so 'super' doesn't work: use
        # direct parent invocation.
        HTMLTranslator.__init__(self, builder, *args, **kwds)

        builder = args[0]
        self.current_docname = str(builder.current_docname)

    def dispatch_visit(self, node: Node) -> None:
        """Override of dispatch_visit.

        Calls appropriate visitor method."""

        for node_class in node.__class__.__mro__:
            method = getattr(self, "visit_%s" % (node_class.__name__), None)
            if method:
                if node.source is not None:
                    # self._report_progress(node)
                    self._add_linemarker_class(node)
                method(node)
                break
        else:
            super().dispatch_visit(node)

    def _add_linemarker_class(self, node):
        if self.current_docname in node.source.replace("\\", "/"):
            if node.line is not None:
                if hasattr(node, "attributes"):
                    node.attributes["classes"].append("linemarker")
                    node.attributes["classes"].append(f"linemarker-{node.line}")
