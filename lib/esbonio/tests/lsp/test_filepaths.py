import itertools
import logging
import unittest.mock as mock

import py.test

from esbonio.lsp.filepaths import FilepathCompletions
from esbonio.lsp.testing import (
    completion_test,
    directive_argument_patterns,
    role_target_patterns,
)

ROOT_FILES = {
    "_static",
    "_templates",
    "theorems",
    "conf.py",
    "index.rst",
    "make.bat",
    "Makefile",
}

THEOREM_FILES = {"index.rst", "pythagoras.rst"}


def trigger_cases(path=None):
    """Expand a path into all roles and directives we wish to test it with."""
    return [
        *role_target_patterns("download", path),
        *directive_argument_patterns("image", path),
        *directive_argument_patterns("figure", path),
        *directive_argument_patterns("include", path),
        *directive_argument_patterns("literalinclude", path),
    ]


@py.test.mark.parametrize(
    "text, setup",
    [
        *itertools.product(
            [*trigger_cases("/"), *trigger_cases("/conf")],
            [
                (
                    "sphinx-default",
                    "index.rst",
                    ROOT_FILES,
                    None,
                ),
                (
                    "sphinx-default",
                    "theorems/pythagoras.rst",
                    ROOT_FILES,
                    None,
                ),
            ],
        ),
        *itertools.product(
            trigger_cases(),
            [
                (
                    "sphinx-default",
                    "index.rst",
                    ROOT_FILES,
                    None,
                ),
                (
                    "sphinx-default",
                    "theorems/pythagoras.rst",
                    THEOREM_FILES,
                    None,
                ),
            ],
        ),
        *itertools.product(
            trigger_cases("../"),
            [
                (
                    "sphinx-default",
                    "theorems/pythagoras.rst",
                    ROOT_FILES,
                    None,
                ),
                (
                    "sphinx-default",
                    "index.rst",
                    {"sphinx-default", "sphinx-extensions"},
                    None,
                ),
            ],
        ),
        *itertools.product(
            trigger_cases("/theorems/"),
            [
                (
                    "sphinx-default",
                    "index.rst",
                    THEOREM_FILES,
                    None,
                ),
                (
                    "sphinx-default",
                    "theorems/pythagoras.rst",
                    THEOREM_FILES,
                    None,
                ),
            ],
        ),
    ],
)
def test_filepath_completions(sphinx, text, setup):
    """Ensure that we can offer correct filepath suggestions."""

    project, filepath, expected, unexpected = setup

    rst = mock.Mock()
    rst.app = sphinx(project)
    rst.logger = logging.getLogger("rst")

    feature = FilepathCompletions(rst)
    completion_test(
        feature, text, filepath=filepath, expected=expected, unexpected=unexpected
    )
