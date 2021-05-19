import itertools
import logging
import unittest.mock as mock

import py.test

from esbonio.lsp.intersphinx import InterSphinx
from esbonio.lsp.testing import completion_test
from esbonio.lsp.testing import intersphinx_target_patterns
from esbonio.lsp.testing import role_target_patterns


@py.test.fixture(scope="session")
def intersphinx(sphinx):
    """Fixture that returns the ``InterSphinx`` feature for a given project.

    Indexing the inventories for every test case adds a noticable overhead
    to the test suite and we don't really gain much from it. This caches instances
    based on project to speed things up.
    """

    instances = {}

    def cache(project):

        if project in instances:
            return instances[project]

        rst = mock.Mock()
        rst.app = sphinx(project)
        rst.logger = logging.getLogger("rst")

        feature = InterSphinx(rst)
        feature.initialize(None)
        instances[project] = feature

        return feature

    return cache


@py.test.mark.parametrize(
    "text, setup",
    [
        # Standard domain
        *itertools.product(
            role_target_patterns("doc"),
            [
                ("sphinx-default", set(), {"python", "sphinx"}),
                ("sphinx-extensions", {"python", "sphinx"}, set()),
            ],
        ),
        *itertools.product(
            role_target_patterns("download"),
            [
                ("sphinx-default", set(), {"python", "sphinx"}),
                ("sphinx-extensions", set(), {"python", "sphinx"}),
            ],
        ),
        *itertools.product(
            role_target_patterns("ref"),
            [
                ("sphinx-default", set(), {"python", "sphinx"}),
                ("sphinx-extensions", {"python", "sphinx"}, set()),
            ],
        ),
        *itertools.product(
            role_target_patterns("func"),
            [
                ("sphinx-default", set(), {"python", "shphinx"}),
                ("sphinx-extensions", {"python", "sphinx"}, set()),
            ],
        ),
    ],
)
def test_project_completions(intersphinx, text, setup):
    """Ensure that we can offer the correct project completions."""

    project, expected, unexpected = setup
    feature = intersphinx(project)

    completion_test(feature, text, expected=expected, unexpected=unexpected)


@py.test.mark.parametrize(
    "text,setup",
    [
        *itertools.product(
            [
                *intersphinx_target_patterns("ref", "python"),
                *intersphinx_target_patterns("std:ref", "python"),
            ],
            [
                (
                    "sphinx-default",
                    set(),
                    {"configparser-objects", "types", "whatsnew-index"},
                ),
                (
                    "sphinx-extensions",
                    {"configparser-objects", "types", "whatsnew-index"},
                    set(),
                ),
            ],
        ),
        *itertools.product(
            [
                *intersphinx_target_patterns("ref", "sphinx"),
                *intersphinx_target_patterns("std:ref", "sphinx"),
            ],
            [
                (
                    "sphinx-default",
                    set(),
                    {
                        "basic-domain-markup",
                        "extension-tutorials-index",
                        "writing-builders",
                    },
                ),
                (
                    "sphinx-extensions",
                    {
                        "basic-domain-markup",
                        "extension-tutorials-index",
                        "writing-builders",
                    },
                    set(),
                ),
            ],
        ),
        *itertools.product(
            intersphinx_target_patterns("func", "python"),
            [
                (
                    "sphinx-default",
                    set(),
                    {"_Py_c_sum", "PyErr_Print", "PyUnicode_Count"},
                ),
                (
                    "sphinx-extensions",
                    {"_Py_c_sum", "PyErr_Print", "PyUnicode_Count"},
                    set(),
                ),
            ],
        ),
        *itertools.product(
            intersphinx_target_patterns("py:func", "python"),
            [
                (
                    "sphinx-default",
                    set(),
                    {"abc.abstractmethod", "msvcrt.locking", "types.new_class"},
                ),
                (
                    "sphinx-extensions",
                    {"abc.abstractmethod", "msvcrt.locking", "types.new_class"},
                    set(),
                ),
            ],
        ),
    ],
)
def test_target_completions(intersphinx, text, setup):
    """Ensure that we can offer the correct target completions."""
    project, expected, unexpected = setup
    feature = intersphinx(project)

    completion_test(feature, text, expected=expected, unexpected=unexpected)
