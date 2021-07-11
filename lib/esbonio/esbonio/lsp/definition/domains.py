import pathlib
import re
from typing import List
from typing import Optional

import pygls.uris as Uri
from docutils.parsers.rst import nodes
from pygls.lsp.types import Location
from pygls.lsp.types import Position
from pygls.lsp.types import Range
from pygls.workspace import Document

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

        target = match.groupdict()["target"]

        if name == "ref":
            return self.ref_definition(target)

        if name == "doc":
            return self.doc_definition(doc, target)

        return super().find_definitions(doc, match, name, domain=domain)

    def doc_definition(self, doc: Document, target: str) -> List[Location]:
        """Goto definition implementation for ``:doc:`` targets"""

        srcdir = self.rst.app.srcdir
        currentdir = pathlib.Path(Uri.to_fs_path(doc.uri)).parent

        if target.startswith("/"):
            path = str(pathlib.Path(srcdir, target[1:] + ".rst"))
        else:
            path = str(pathlib.Path(currentdir, target + ".rst"))

        return [
            Location(
                uri=Uri.from_fs_path(path),
                range=Range(
                    start=Position(line=0, character=0),
                    end=Position(line=1, character=0),
                ),
            )
        ]

    def ref_definition(self, target: str) -> List[Location]:
        """Goto definition implementation for ``:ref:`` targets"""

        std = self.rst.get_domain("std")
        types = set(self.rst.get_role_target_types("ref"))

        uri = None
        line = None
        docname = None

        if not std:
            return []

        # _, title, _, _, anchor, priority
        for name, _, type_, doc, _, _ in std.get_objects():
            if type_ not in types:
                continue

            if name == target:
                docname = doc
                break

        doctree = self.rst.get_doctree(docname)
        for node in doctree.traverse(condition=nodes.target):

            if "refid" not in node:
                continue

            if target == node["refid"].replace("-", "_"):
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
