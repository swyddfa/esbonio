from __future__ import annotations

import hashlib
import logging
import os
import pathlib
import sys
import typing
from unittest import mock

import pytest
from sphinx import version_info as sphinx_version

from esbonio.sphinx_agent.config import SphinxConfig
from esbonio.sphinx_agent.log import DiagnosticFilter
from esbonio.sphinx_agent.log import source_to_uri_and_linum
from esbonio.sphinx_agent.types import Uri

if typing.TYPE_CHECKING:
    from typing import Any


logger = logging.getLogger(__name__)


sphinx_lt_81 = sphinx_version[0] < 8 or (
    sphinx_version[0] == 8 and sphinx_version[1] < 1
)


def application_args(**kwargs) -> dict[str, Any]:
    defaults = {
        "confoverrides": {},
        "freshenv": False,
        "keep_going": False,
        "parallel": 1,
        "tags": [],
        "verbosity": 0,
        "warningiserror": False,
    }

    for arg in ("srcdir", "outdir", "confdir", "doctreedir"):
        if arg in kwargs:
            kwargs[arg] = str(pathlib.Path(kwargs[arg]).resolve())

    # Order matters, kwargs will override any keys found in defaults.
    return {**defaults, **kwargs}


@pytest.mark.parametrize(
    "args, expected",
    [
        (
            ["-M", "html", "src", "out"],
            application_args(
                srcdir="src",
                confdir="src",
                outdir=os.path.join("out", "html"),
                doctreedir=os.path.join("out", "doctrees"),
                buildername="html",
            ),
        ),
        (
            ["-M", "latex", "src", "out"],
            application_args(
                srcdir="src",
                confdir="src",
                outdir=os.path.join("out", "latex"),
                doctreedir=os.path.join("out", "doctrees"),
                buildername="latex",
            ),
        ),
        (
            ["-M", "html", "src", "out", "-E"],
            application_args(
                srcdir="src",
                confdir="src",
                outdir=os.path.join("out", "html"),
                doctreedir=os.path.join("out", "doctrees"),
                buildername="html",
                freshenv=True,
            ),
        ),
        (
            ["-M", "html", "src", "out", "-c", "conf"],
            application_args(
                srcdir="src",
                confdir="conf",
                outdir=os.path.join("out", "html"),
                doctreedir=os.path.join("out", "doctrees"),
                buildername="html",
            ),
        ),
        (
            ["-M", "html", "src", "out", "-d", "doctreedir"],
            application_args(
                srcdir="src",
                confdir="src",
                outdir=os.path.join("out", "html"),
                doctreedir="doctreedir",
                buildername="html",
            ),
        ),
        (
            ["-M", "html", "src", "out", "-Dkey=value", "-Danother=v"],
            application_args(
                srcdir="src",
                confdir="src",
                outdir=os.path.join("out", "html"),
                doctreedir=os.path.join("out", "doctrees"),
                buildername="html",
                confoverrides=dict(
                    key="value",
                    another="v",
                ),
            ),
        ),
        (
            ["-M", "html", "src", "out", "-Akey=value", "-Aanother=v"],
            application_args(
                srcdir="src",
                confdir="src",
                outdir=os.path.join("out", "html"),
                doctreedir=os.path.join("out", "doctrees"),
                buildername="html",
                confoverrides={
                    "html_context.key": "value",
                    "html_context.another": "v",
                },
            ),
        ),
        (
            ["-M", "html", "src", "out", "-j", "4"],
            application_args(
                srcdir="src",
                confdir="src",
                outdir=os.path.join("out", "html"),
                doctreedir=os.path.join("out", "doctrees"),
                buildername="html",
                parallel=4,
            ),
        ),
        (
            ["-M", "html", "src", "out", "-n"],
            application_args(
                srcdir="src",
                confdir="src",
                outdir=os.path.join("out", "html"),
                doctreedir=os.path.join("out", "doctrees"),
                buildername="html",
                confoverrides=dict(nitpicky=True),
            ),
        ),
        (
            # quiet = True is handled by the logging framework
            ["-M", "html", "src", "out", "-q"],
            application_args(
                srcdir="src",
                confdir="src",
                outdir=os.path.join("out", "html"),
                doctreedir=os.path.join("out", "doctrees"),
                buildername="html",
            ),
        ),
        (
            # silent = True is handled by the logging framework
            ["-M", "html", "src", "out", "-Q"],
            application_args(
                srcdir="src",
                confdir="src",
                outdir=os.path.join("out", "html"),
                doctreedir=os.path.join("out", "doctrees"),
                buildername="html",
            ),
        ),
        (
            ["-M", "html", "src", "out", "-t", "tag1"],
            application_args(
                srcdir="src",
                confdir="src",
                outdir=os.path.join("out", "html"),
                doctreedir=os.path.join("out", "doctrees"),
                buildername="html",
                tags=["tag1"],
            ),
        ),
        (
            ["-M", "html", "src", "out", "-t", "tag1", "-t", "tag2"],
            application_args(
                srcdir="src",
                confdir="src",
                outdir=os.path.join("out", "html"),
                doctreedir=os.path.join("out", "doctrees"),
                buildername="html",
                tags=["tag1", "tag2"],
            ),
        ),
        (
            ["-M", "html", "src", "out", "-v"],
            application_args(
                srcdir="src",
                confdir="src",
                outdir=os.path.join("out", "html"),
                doctreedir=os.path.join("out", "doctrees"),
                buildername="html",
                verbosity=1,
            ),
        ),
        (
            ["-M", "html", "src", "out", "-vvv"],
            application_args(
                srcdir="src",
                confdir="src",
                outdir=os.path.join("out", "html"),
                doctreedir=os.path.join("out", "doctrees"),
                buildername="html",
                verbosity=3,
            ),
        ),
        (
            ["-M", "html", "src", "out", "-W"],
            application_args(
                srcdir="src",
                confdir="src",
                outdir=os.path.join("out", "html"),
                doctreedir=os.path.join("out", "doctrees"),
                buildername="html",
                warningiserror=True,
            ),
        ),
        (
            ["-M", "html", "src", "out", "-W", "--keep-going"],
            application_args(
                srcdir="src",
                confdir="src",
                outdir=os.path.join("out", "html"),
                doctreedir=os.path.join("out", "doctrees"),
                buildername="html",
                warningiserror=True,
                # --keep-going ignored since v8.1
                # https://github.com/sphinx-doc/sphinx/pull/12743/files#diff-4aea2ac365ab5325b530ac42efc67feac98db110e7f943ea13b5cf88f4260e59
                keep_going=sphinx_lt_81,
            ),
        ),
        (
            ["-b", "html", "src", "out"],
            application_args(
                srcdir="src",
                confdir="src",
                outdir="out",
                doctreedir=os.path.join("out", ".doctrees"),
                buildername="html",
            ),
        ),
        (
            ["-b", "latex", "src", "out"],
            application_args(
                srcdir="src",
                confdir="src",
                outdir="out",
                doctreedir=os.path.join("out", ".doctrees"),
                buildername="latex",
            ),
        ),
        (
            ["-b", "html", "-E", "src", "out"],
            application_args(
                srcdir="src",
                confdir="src",
                outdir="out",
                doctreedir=os.path.join("out", ".doctrees"),
                buildername="html",
                freshenv=True,
            ),
        ),
        (
            ["-b", "html", "-c", "conf", "src", "out"],
            application_args(
                srcdir="src",
                confdir="conf",
                outdir="out",
                doctreedir=os.path.join("out", ".doctrees"),
                buildername="html",
            ),
        ),
        (
            ["-b", "html", "-Dkey=value", "-Danother=v", "src", "out"],
            application_args(
                srcdir="src",
                confdir="src",
                outdir="out",
                doctreedir=os.path.join("out", ".doctrees"),
                buildername="html",
                confoverrides=dict(
                    key="value",
                    another="v",
                ),
            ),
        ),
        (
            ["-b", "html", "-Akey=value", "-Aanother=v", "src", "out"],
            application_args(
                srcdir="src",
                confdir="src",
                outdir="out",
                doctreedir=os.path.join("out", ".doctrees"),
                buildername="html",
                confoverrides={
                    "html_context.key": "value",
                    "html_context.another": "v",
                },
            ),
        ),
        (
            ["-b", "html", "-d", "doctreedir", "src", "out"],
            application_args(
                srcdir="src",
                confdir="src",
                outdir="out",
                doctreedir="doctreedir",
                buildername="html",
            ),
        ),
        (
            ["-b", "html", "-j", "4", "src", "out"],
            application_args(
                srcdir="src",
                confdir="src",
                outdir="out",
                doctreedir=os.path.join("out", ".doctrees"),
                buildername="html",
                parallel=4,
            ),
        ),
        (
            ["-b", "html", "-n", "src", "out"],
            application_args(
                srcdir="src",
                confdir="src",
                outdir="out",
                doctreedir=os.path.join("out", ".doctrees"),
                buildername="html",
                confoverrides={
                    "nitpicky": True,
                },
            ),
        ),
        (
            ["-b", "html", "-q", "src", "out"],
            application_args(
                srcdir="src",
                confdir="src",
                outdir="out",
                doctreedir=os.path.join("out", ".doctrees"),
                buildername="html",
            ),
        ),
        (
            ["-b", "html", "-Q", "src", "out"],
            application_args(
                srcdir="src",
                confdir="src",
                outdir="out",
                doctreedir=os.path.join("out", ".doctrees"),
                buildername="html",
            ),
        ),
        (
            ["-b", "html", "-t", "tag1", "src", "out"],
            application_args(
                srcdir="src",
                confdir="src",
                outdir="out",
                doctreedir=os.path.join("out", ".doctrees"),
                buildername="html",
                tags=["tag1"],
            ),
        ),
        (
            ["-b", "html", "-t", "tag1", "-t", "tag2", "src", "out"],
            application_args(
                srcdir="src",
                confdir="src",
                outdir="out",
                doctreedir=os.path.join("out", ".doctrees"),
                buildername="html",
                tags=["tag1", "tag2"],
            ),
        ),
        (
            ["-b", "html", "-v", "src", "out"],
            application_args(
                srcdir="src",
                confdir="src",
                outdir="out",
                doctreedir=os.path.join("out", ".doctrees"),
                buildername="html",
                verbosity=1,
            ),
        ),
        (
            ["-b", "html", "-vvv", "src", "out"],
            application_args(
                srcdir="src",
                confdir="src",
                outdir="out",
                doctreedir=os.path.join("out", ".doctrees"),
                buildername="html",
                verbosity=3,
            ),
        ),
        (
            ["-b", "html", "-W", "src", "out"],
            application_args(
                srcdir="src",
                confdir="src",
                outdir="out",
                doctreedir=os.path.join("out", ".doctrees"),
                buildername="html",
                warningiserror=True,
            ),
        ),
        (
            ["-b", "html", "-W", "--keep-going", "src", "out"],
            application_args(
                srcdir="src",
                confdir="src",
                outdir="out",
                doctreedir=os.path.join("out", ".doctrees"),
                buildername="html",
                warningiserror=True,
                # --keep-going ignored since v8.1
                # https://github.com/sphinx-doc/sphinx/pull/12743/files#diff-4aea2ac365ab5325b530ac42efc67feac98db110e7f943ea13b5cf88f4260e59
                keep_going=sphinx_lt_81,
            ),
        ),
    ],
)
def test_cli_arg_handling(args: list[str], expected: dict[str, Any]):
    """Ensure that we can convert ``sphinx-build`` to the correct Sphinx application
    options."""
    config = SphinxConfig.fromcli(args)
    assert config is not None

    actual = config.to_application_args({})

    # pytest overrides stderr on windows, so if we were to put `sys.stderr` in the
    # `expected` dict this test would fail as `sys.stderr` inside a test function has a
    # different value.
    #
    # So, let's test for it here instead
    assert actual.pop("status") == sys.stderr
    assert actual.pop("warning") == sys.stderr

    assert expected == actual


@pytest.mark.parametrize(
    "args, expected, context",
    [
        (
            ["-M", "html", "src", "${defaultBuildDir}"],
            application_args(
                srcdir="src",
                confdir="src",
                outdir=os.sep + os.path.join("path", "to", "cache", "<HASH>", "html"),
                doctreedir=(
                    os.sep + os.path.join("path", "to", "cache", "<HASH>", "doctrees")
                ),
                buildername="html",
            ),
            {
                "cacheDir": os.sep + os.sep.join(["path", "to", "cache"]),
            },
        ),
        (
            ["-M", "html", "src", "${defaultBuildDir}"],
            application_args(
                srcdir="src",
                confdir="src",
                outdir=os.sep + os.path.join("path", "to", ".cache", "<HASH>", "html"),
                doctreedir=(
                    os.sep + os.path.join("path", "to", ".cache", "<HASH>", "doctrees")
                ),
                buildername="html",
            ),
            {
                "cacheDir": os.sep + os.sep.join(["path", "to", ".cache"]),
            },
        ),
        (
            ["-b", "html", "src", "${defaultBuildDir}"],
            application_args(
                srcdir="src",
                confdir="src",
                outdir=os.sep + os.sep.join(["path", "to", "cache", "<HASH>"]),
                doctreedir=(
                    os.sep + os.path.join("path", "to", "cache", r"<HASH>", ".doctrees")
                ),
                buildername="html",
            ),
            {
                "cacheDir": os.sep + os.sep.join(["path", "to", "cache"]),
            },
        ),
        (
            ["-b", "html", "src", "${defaultBuildDir}"],
            application_args(
                srcdir="src",
                confdir="src",
                outdir=os.sep + os.sep.join(["path", "to", ".cache", "<HASH>"]),
                doctreedir=(
                    os.sep
                    + os.path.join("path", "to", ".cache", r"<HASH>", ".doctrees")
                ),
                buildername="html",
            ),
            {
                "cacheDir": os.sep + os.sep.join(["path", "to", ".cache"]),
            },
        ),
    ],
)
def test_cli_default_build_dir(
    args: list[str], expected: dict[str, Any], context: dict[str, str]
):
    """Ensure that we can handle ``${defaultBuildDir}`` variable correctly."""
    config = SphinxConfig.fromcli(args)
    assert config is not None

    actual = config.to_application_args(context)

    # pytest overrides stderr on windows, so if we were to put `sys.stderr` in the
    # `expected` dict this test would fail as `sys.stderr` inside a test function has a
    # different value.
    #
    # So, let's test for it here instead
    assert actual.pop("status") == sys.stderr
    assert actual.pop("warning") == sys.stderr

    # Compute the expected hash now that the confdir has been resolved
    ehash = hashlib.md5(config.conf_dir.encode()).hexdigest()
    expected["outdir"] = expected["outdir"].replace("<HASH>", ehash)
    expected["doctreedir"] = expected["doctreedir"].replace("<HASH>", ehash)

    assert expected == actual


ROOT = pathlib.Path(__file__).parent.parent / "sphinx-extensions" / "workspace"
PY_PATH = ROOT / "code" / "diagnostics.py"
CONF_PATH = ROOT / "sphinx-extensions" / "conf.py"
RST_PATH = ROOT / "sphinx-extensions" / "index.rst"
INC_PATH = ROOT / "sphinx-extensions" / "_include_me.txt"
REL_INC_PATH = os.path.relpath(INC_PATH)


@pytest.mark.parametrize(
    "location, expected",
    [
        (f"{RST_PATH}", (Uri.for_file(RST_PATH), None)),
        (f"{RST_PATH}:", (Uri.for_file(RST_PATH), None)),
        (f"{RST_PATH}:3", (Uri.for_file(RST_PATH), 3)),
        (f"{REL_INC_PATH}:12", (Uri.for_file(INC_PATH), 12)),
        (
            f"{PY_PATH}:docstring of esbonio.sphinx_agent.log.DiagnosticFilter:3",
            (Uri.for_file(PY_PATH), 22),
        ),
        (f"internal padding after {RST_PATH}:34", (Uri.for_file(RST_PATH), 34)),
        (f"internal padding before {RST_PATH}:34", (Uri.for_file(RST_PATH), 34)),
    ],
)
def test_source_to_uri_linum(location: str, expected: tuple[str, int | None]):
    """Ensure we can correctly determine a dianostic's location based on the string we
    get from sphinx."""

    mockpath = f"{DiagnosticFilter.__module__}.inspect.getsourcelines"
    with mock.patch(mockpath, return_value=([""], 20)):
        actual = source_to_uri_and_linum(location)

    assert actual == expected
