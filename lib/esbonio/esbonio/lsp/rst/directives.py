import importlib
import json
from typing import Dict
from typing import Optional
from typing import Tuple
from typing import Union

import pkg_resources
from docutils.parsers.rst import Directive
from docutils.parsers.rst import directives as docutils_directives

from esbonio.lsp.directives import DirectiveLanguageFeature
from esbonio.lsp.directives import Directives


class Docutils(DirectiveLanguageFeature):
    """Support for docutils' built-in directives."""

    def __init__(self) -> None:

        self._directives: Optional[Dict[str, Directive]] = None
        """Cache for known directives."""

    @property
    def directives(self) -> Dict[str, Directive]:
        if self._directives is not None:
            return self._directives

        ignored_directives = ["restructuredtext-test-directive"]
        found_directives = {
            **docutils_directives._directive_registry,
            **docutils_directives._directives,
        }

        self._directives = {
            k: resolve_directive(v)
            for k, v in found_directives.items()
            if k not in ignored_directives
        }

        return self._directives

    def get_implementation(self, directive: str, domain: Optional[str]):
        if domain:
            return None

        return self.directives.get(directive, None)

    def index_directives(self) -> Dict[str, Directive]:
        return self.directives


def resolve_directive(directive: Union[Directive, Tuple[str, str]]) -> Directive:
    """Return the directive based on the given reference.

    'Core' docutils directives are returned as tuples ``(modulename, ClassName)``
    so they need to be resolved manually.
    """

    if isinstance(directive, tuple):
        mod, cls = directive

        modulename = "docutils.parsers.rst.directives.{}".format(mod)
        module = importlib.import_module(modulename)
        return getattr(module, cls)

    return directive


def esbonio_setup(directives: Directives):
    documentation = pkg_resources.resource_string("esbonio.lsp.rst", "directives.json")

    directives.add_documentation(json.loads(documentation.decode("utf8")))
    directives.add_feature(Docutils())
