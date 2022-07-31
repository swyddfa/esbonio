import itertools
import os
import pathlib
from typing import List
from typing import Optional
from typing import Tuple
from unittest import mock

import pygls.uris as uri
import pytest
from pygls import IS_WIN

from esbonio.lsp.sphinx import SphinxConfig
from esbonio.lsp.sphinx import SphinxLogHandler


def config_with(**kwargs) -> SphinxConfig:
    """Return a SphinxConfig object with the given config dir."""

    args = {k: str(v) if isinstance(v, pathlib.Path) else v for k, v in kwargs.items()}
    for dir_ in ["buildDir", "confDir", "doctreeDir", "srcDir"]:
        if dir_ not in args:
            args[dir_] = str(
                pathlib.Path(f"/path/to/{dir_.replace('Dir', '')}").resolve()
            )

    return SphinxConfig(**args)


@pytest.mark.parametrize(
    "root_uri, setup",
    [
        *itertools.product(
            ["file:///path/to/root"],
            [
                # buildDir handling
                (
                    config_with(buildDir="/path/to/build"),
                    config_with(buildDir=pathlib.Path("/path/to/build/html")),
                ),
                (
                    config_with(buildDir="~/path/to/build"),
                    config_with(
                        buildDir=pathlib.Path("~/path/to/build/html").expanduser()
                    ),
                ),
                (
                    config_with(buildDir="${workspaceRoot}/build"),
                    config_with(
                        buildDir=pathlib.Path("/path/to/root/build/html").resolve()
                    ),
                ),
                (
                    config_with(buildDir="${workspaceRoot}/../build"),
                    config_with(buildDir=pathlib.Path("/path/to/build/html").resolve()),
                ),
                (
                    config_with(buildDir="${workspaceFolder}/build"),
                    config_with(
                        buildDir=pathlib.Path("/path/to/root/build/html").resolve()
                    ),
                ),
                (
                    config_with(buildDir="${workspaceFolder}/../build"),
                    config_with(buildDir=pathlib.Path("/path/to/build/html").resolve()),
                ),
                (
                    config_with(buildDir="${confDir}/build"),
                    config_with(
                        buildDir=pathlib.Path("/path/to/conf/build/html").resolve()
                    ),
                ),
                (
                    config_with(buildDir="${confDir}/../build"),
                    config_with(buildDir=pathlib.Path("/path/to/build/html").resolve()),
                ),
                (
                    config_with(buildDir="/path/to/build", makeMode=False),
                    config_with(
                        buildDir=pathlib.Path("/path/to/build"), makeMode=False
                    ),
                ),
                # confDir handling
                (
                    config_with(confDir="/path/to/config"),
                    config_with(
                        buildDir=pathlib.Path("/path/to/build/html").resolve(),
                        confDir=pathlib.Path("/path/to/config"),
                    ),
                ),
                (
                    config_with(confDir="~/path/to/config"),
                    config_with(
                        buildDir=pathlib.Path("/path/to/build/html").resolve(),
                        confDir=pathlib.Path("~/path/to/config").expanduser(),
                    ),
                ),
                (
                    config_with(confDir="${workspaceRoot}/config"),
                    config_with(
                        buildDir=pathlib.Path("/path/to/build/html").resolve(),
                        confDir=pathlib.Path("/path/to/root/config").resolve(),
                    ),
                ),
                (
                    config_with(confDir="${workspaceRoot}/../config"),
                    config_with(
                        buildDir=pathlib.Path("/path/to/build/html").resolve(),
                        confDir=pathlib.Path("/path/to/config").resolve(),
                    ),
                ),
                (
                    config_with(confDir="${workspaceFolder}/config"),
                    config_with(
                        buildDir=pathlib.Path("/path/to/build/html").resolve(),
                        confDir=pathlib.Path("/path/to/root/config").resolve(),
                    ),
                ),
                (
                    config_with(confDir="${workspaceFolder}/../config"),
                    config_with(
                        buildDir=pathlib.Path("/path/to/build/html").resolve(),
                        confDir=pathlib.Path("/path/to/config").resolve(),
                    ),
                ),
                # doctreeDir handling (make mode)
                (
                    config_with(buildDir="/path/to/build", doctreeDir=None),
                    config_with(
                        buildDir=pathlib.Path("/path/to/build/html"),
                        doctreeDir=pathlib.Path("/path/to/build/doctrees"),
                    ),
                ),
                (
                    config_with(
                        buildDir="/path/to/build", doctreeDir="/path/to/doctrees"
                    ),
                    config_with(
                        buildDir=pathlib.Path("/path/to/build/html"),
                        doctreeDir=pathlib.Path("/path/to/doctrees"),
                    ),
                ),
                (
                    config_with(
                        buildDir="/path/to/build",
                        doctreeDir="${workspaceRoot}/doctrees",
                    ),
                    config_with(
                        buildDir=pathlib.Path("/path/to/build/html"),
                        doctreeDir=pathlib.Path("/path/to/root/doctrees").resolve(),
                    ),
                ),
                (
                    config_with(
                        buildDir="/path/to/build",
                        doctreeDir="${workspaceFolder}/../dts",
                    ),
                    config_with(
                        buildDir=pathlib.Path("/path/to/build/html"),
                        doctreeDir=pathlib.Path("/path/to/dts").resolve(),
                    ),
                ),
                (
                    config_with(
                        buildDir="/path/to/build",
                        doctreeDir="${confDir}/dts",
                    ),
                    config_with(
                        buildDir=pathlib.Path("/path/to/build/html"),
                        doctreeDir=pathlib.Path("/path/to/conf/dts").resolve(),
                    ),
                ),
                (
                    config_with(
                        buildDir="/path/to/build",
                        doctreeDir="${buildDir}/dts",
                    ),
                    config_with(
                        buildDir=pathlib.Path("/path/to/build/html"),
                        doctreeDir=pathlib.Path("/path/to/build/dts").resolve(),
                    ),
                ),
                # doctreeDir handling (non make mode)
                (
                    config_with(
                        buildDir="/path/to/build", doctreeDir=None, makeMode=False
                    ),
                    config_with(
                        buildDir=pathlib.Path("/path/to/build"),
                        doctreeDir=pathlib.Path("/path/to/build/.doctrees"),
                        makeMode=False,
                    ),
                ),
                (
                    config_with(
                        buildDir="/path/to/build",
                        doctreeDir="/path/to/doctrees",
                        makeMode=False,
                    ),
                    config_with(
                        buildDir=pathlib.Path("/path/to/build"),
                        doctreeDir=pathlib.Path("/path/to/doctrees"),
                        makeMode=False,
                    ),
                ),
                (
                    config_with(
                        buildDir="/path/to/build",
                        doctreeDir="${workspaceRoot}/doctrees",
                        makeMode=False,
                    ),
                    config_with(
                        buildDir=pathlib.Path("/path/to/build"),
                        doctreeDir=pathlib.Path("/path/to/root/doctrees").resolve(),
                        makeMode=False,
                    ),
                ),
                (
                    config_with(
                        buildDir="/path/to/build",
                        doctreeDir="${workspaceFolder}/../dts",
                        makeMode=False,
                    ),
                    config_with(
                        buildDir=pathlib.Path("/path/to/build"),
                        doctreeDir=pathlib.Path("/path/to/dts").resolve(),
                        makeMode=False,
                    ),
                ),
                (
                    config_with(
                        buildDir="/path/to/build",
                        doctreeDir="${confDir}/../dts",
                        makeMode=False,
                    ),
                    config_with(
                        buildDir=pathlib.Path("/path/to/build"),
                        doctreeDir=pathlib.Path("/path/to/dts").resolve(),
                        makeMode=False,
                    ),
                ),
                (
                    config_with(
                        buildDir="/path/to/build",
                        doctreeDir="${buildDir}/dts",
                        makeMode=False,
                    ),
                    config_with(
                        buildDir=pathlib.Path("/path/to/build"),
                        doctreeDir=pathlib.Path("/path/to/build/dts").resolve(),
                        makeMode=False,
                    ),
                ),
                # srcDir handling
                (
                    config_with(srcDir="/path/to/src"),
                    config_with(
                        buildDir=pathlib.Path("/path/to/build/html").resolve(),
                        srcDir=pathlib.Path("/path/to/src"),
                    ),
                ),
                (
                    config_with(srcDir="~/path/to/src"),
                    config_with(
                        buildDir=pathlib.Path("/path/to/build/html").resolve(),
                        srcDir=pathlib.Path("~/path/to/src").expanduser(),
                    ),
                ),
                (
                    config_with(srcDir="${workspaceRoot}/src"),
                    config_with(
                        buildDir=pathlib.Path("/path/to/build/html").resolve(),
                        srcDir=pathlib.Path("/path/to/root/src").resolve(),
                    ),
                ),
                (
                    config_with(srcDir="${workspaceRoot}/../src"),
                    config_with(
                        buildDir=pathlib.Path("/path/to/build/html").resolve(),
                        srcDir=pathlib.Path("/path/to/src").resolve(),
                    ),
                ),
                (
                    config_with(srcDir="${workspaceFolder}/src"),
                    config_with(
                        buildDir=pathlib.Path("/path/to/build/html").resolve(),
                        srcDir=pathlib.Path("/path/to/root/src").resolve(),
                    ),
                ),
                (
                    config_with(srcDir="${workspaceFolder}/../src"),
                    config_with(
                        buildDir=pathlib.Path("/path/to/build/html").resolve(),
                        srcDir=pathlib.Path("/path/to/src").resolve(),
                    ),
                ),
                (
                    config_with(srcDir="${confDir}/src"),
                    config_with(
                        buildDir=pathlib.Path("/path/to/build/html").resolve(),
                        srcDir=pathlib.Path("/path/to/conf/src").resolve(),
                    ),
                ),
                (
                    config_with(srcDir="${confDir}/../src"),
                    config_with(
                        buildDir=pathlib.Path("/path/to/build/html").resolve(),
                        srcDir=pathlib.Path("/path/to/src").resolve(),
                    ),
                ),
            ],
        )
    ],
)
def test_resolve(root_uri, setup: Tuple[SphinxConfig, SphinxConfig]):
    """Ensure that we can resolve a config relative to a project root correctly."""
    config, expected = setup
    actual = config.resolve(root_uri)

    # This seems hacky, but paths on windows are case insensitive...
    if IS_WIN:
        assert expected.build_dir.lower() == actual.build_dir.lower()
        assert expected.conf_dir.lower() == actual.conf_dir.lower()
        assert expected.doctree_dir.lower() == actual.doctree_dir.lower()
        assert expected.src_dir.lower() == actual.src_dir.lower()

    else:
        assert expected.build_dir == actual.build_dir
        assert expected.conf_dir == actual.conf_dir
        assert expected.doctree_dir == actual.doctree_dir
        assert expected.src_dir == actual.src_dir

    assert expected.builder_name == actual.builder_name
    assert expected.config_overrides == actual.config_overrides
    assert expected.force_full_build == actual.force_full_build
    assert expected.keep_going == actual.keep_going
    assert expected.make_mode == actual.make_mode
    assert expected.num_jobs == actual.num_jobs
    assert expected.quiet == actual.quiet
    assert expected.silent == actual.silent
    assert expected.tags == actual.tags
    assert expected.verbosity == actual.verbosity
    assert expected.warning_is_error == actual.warning_is_error


@pytest.mark.parametrize(
    "args",
    [
        ["-M", "html", "src", "out"],
        ["-M", "latex", "src", "out"],
        ["-M", "html", "src", "out", "-E"],
        ["-M", "html", "src", "out", "-c", "conf"],
        ["-M", "html", "src", "out", "-d", "doctreedir"],
        ["-M", "html", "src", "out", "-Dkey=value", "-Danother=v"],
        ["-M", "html", "src", "out", "-Akey=value", "-Aanother=v"],
        ["-M", "html", "src", "out", "-j", "4"],
        ["-M", "html", "src", "out", "-n"],
        ["-M", "html", "src", "out", "-q"],
        ["-M", "html", "src", "out", "-Q"],
        ["-M", "html", "src", "out", "-t", "tag1"],
        ["-M", "html", "src", "out", "-t", "tag1", "-t", "tag2"],
        ["-M", "html", "src", "out", "-v"],
        ["-M", "html", "src", "out", "-vv"],
        ["-M", "html", "src", "out", "-vvv"],
        ["-M", "html", "src", "out", "-W"],
        ["-M", "html", "src", "out", "-W", "--keep-going"],
        ["-b", "html", "src", "out"],
        ["-b", "latex", "src", "out"],
        ["-b", "html", "-E", "src", "out"],
        ["-b", "html", "-c", "conf", "src", "out"],
        ["-b", "html", "-Dkey=value", "-Danother=v", "src", "out"],
        ["-b", "html", "-Akey=value", "-Aanother=v", "src", "out"],
        ["-b", "html", "-d", "doctreedir", "src", "out"],
        ["-b", "html", "-j", "4", "src", "out"],
        ["-b", "html", "-n", "src", "out"],
        ["-b", "html", "-q", "src", "out"],
        ["-b", "html", "-Q", "src", "out"],
        ["-b", "html", "-t", "tag1", "src", "out"],
        ["-b", "html", "-t", "tag1", "-t", "tag2", "src", "out"],
        ["-b", "html", "-v", "src", "out"],
        ["-b", "html", "-vv", "src", "out"],
        ["-b", "html", "-vvv", "src", "out"],
        ["-b", "html", "-W", "src", "out"],
        ["-b", "html", "-W", "--keep-going", "src", "out"],
    ],
)
def test_cli_arg_handling(args: List[str]):
    """Ensure that we can convert ``sphinx-build`` to initialization options and back."""

    config = SphinxConfig.from_arguments(cli_args=args)
    actual = config.to_cli_args()

    assert args == actual


ROOT = pathlib.Path(__file__).parent.parent / "sphinx-extensions" / "workspace"
PY_PATH = ROOT / "code" / "diagnostics.py"
CONF_PATH = ROOT / "sphinx-extensions" / "conf.py"
RST_PATH = ROOT / "sphinx-extensions" / "index.rst"
INC_PATH = ROOT / "sphinx-extensions" / "_include_me.txt"
REL_INC_PATH = os.path.relpath(INC_PATH)


@pytest.mark.parametrize(
    "location, expected",
    [
        ("", (uri.from_fs_path(str(CONF_PATH)), None)),
        (f"{RST_PATH}", (uri.from_fs_path(str(RST_PATH)), None)),
        (f"{RST_PATH}:", (uri.from_fs_path(str(RST_PATH)), None)),
        (f"{RST_PATH}:3", (uri.from_fs_path(str(RST_PATH)), 3)),
        (f"{REL_INC_PATH}:12", (uri.from_fs_path(str(INC_PATH)), 12)),
        (
            f"{PY_PATH}:docstring of esbonio.lsp.sphinx.config.SphinxLogHandler:3",
            (uri.from_fs_path(str(PY_PATH)), 22),
        ),
        (
            f"internal padding after {RST_PATH}:34",
            (uri.from_fs_path(str(RST_PATH)), 34),
        ),
        (
            f"internal padding before {RST_PATH}:34",
            (uri.from_fs_path(str(RST_PATH)), 34),
        ),
    ],
)
def test_get_diagnostic_location(location: str, expected: Tuple[str, Optional[int]]):
    """Ensure we can correctly determine a dianostic's location based on the string we
    get from sphinx."""

    app = mock.Mock()
    app.confdir = str(ROOT / "sphinx-extensions")

    server = mock.Mock()
    handler = SphinxLogHandler(app, server)

    mockpath = f"{SphinxLogHandler.__module__}.inspect.getsourcelines"
    with mock.patch(mockpath, return_value=([""], 20)):
        actual = handler.get_location(location)

    assert actual == expected
