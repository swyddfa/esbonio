import pathlib
import re
from typing import List
from typing import Optional
from typing import Set

import pygls.uris as Uri
from docutils.parsers.rst import nodes
from pygls.lsp.types import Location
from pygls.lsp.types import Position
from pygls.lsp.types import Range
from pygls.workspace import Document
from sphinx.domains import Domain

from esbonio.lsp.roles import TargetDefinition
from esbonio.lsp.sphinx import SphinxLanguageServer


class Domain(TargetDefinition):
    """Looks up definitions of objects defined under Sphinx domains."""

    def __init__(self, rst: SphinxLanguageServer):
        self.rst = rst
        self.logger = rst.logger.getChild(self.__class__.__name__)

    def find_definitions(
        self, doc: Document, match: "re.Match", name: str, domain: Optional[str]
    ) -> List[Location]:

        label = match.groupdict()["label"]

        if name == "ref":
            return self.ref_definition(label)

        if name == "doc":
            return self.doc_definition(doc, label)

        return super().find_definitions(doc, match, name, domain=domain)

    def doc_definition(self, doc: Document, label: str) -> List[Location]:
        """Goto definition implementation for ``:doc:`` targets"""

        srcdir = self.rst.app.srcdir
        currentdir = pathlib.Path(Uri.to_fs_path(doc.uri)).parent

        if label.startswith("/"):
            path = str(pathlib.Path(srcdir, label[1:] + ".rst"))
        else:
            path = str(pathlib.Path(currentdir, label + ".rst"))

        return [
            Location(
                uri=Uri.from_fs_path(path),
                range=Range(
                    start=Position(line=0, character=0),
                    end=Position(line=1, character=0),
                ),
            )
        ]

    def ref_definition(self, label: str) -> List[Location]:
        """Goto definition implementation for ``:ref:`` targets"""

        std = self.rst.get_domain("std")
        types = set(self.rst.get_role_target_types("ref"))

        docname = self.find_docname_for_label(label, std, types)
        if docname is None:
            return []

        doctree = self.rst.get_doctree(docname=docname)
        if doctree is None:
            return []

        uri = None
        line = None

        for node in doctree.traverse(condition=nodes.target):

            if "refid" not in node:
                continue

            if label == node["refid"].replace("-", "_"):
                uri = Uri.from_fs_path(node.source)
                line = node.line
                break

        if uri is None or line is None:
            return []

        return [
            Location(
                uri=uri,
                range=Range(
                    start=Position(line=line - 1, character=0),
                    end=Position(line=line, character=0),
                ),
            )
        ]

    def find_docname_for_label(
        self, label: str, domain: Domain, types: Optional[Set[str]] = None
    ) -> Optional[str]:
        """Given the label name and domain it belongs to, return the docname its
        definition resides in.

        Parameters
        ----------
        label:
           The label to search for
        domain:
           The domain to search within
        types:
           A collection of object types that the label chould have.
        """

        docname = None
        types = types or set()
        if not domain:
            return []

        # _, title, _, _, anchor, priority
        for name, _, type_, doc, _, _ in domain.get_objects():
            if types and type_ not in types:
                continue

            if name == label:
                docname = doc
                break

        return docname
