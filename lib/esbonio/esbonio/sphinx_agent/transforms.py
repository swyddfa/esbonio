from docutils import nodes
from docutils.transforms import Transform


class LineNumberTransform(Transform):
    """Adds line number markers to html nodes.

    Used to implement sync scrolling
    """

    default_priority = 500

    def apply(self, **kwargs):
        for node in self.document.traverse(nodes.paragraph):
            if node.line:
                node["classes"].append("linemarker")
                node["classes"].append(f"linemarker-{node.line}")
