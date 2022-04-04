import pathlib

import pytest

from esbonio.lsp.sphinx import expand_conf_dir
from esbonio.lsp.sphinx import get_build_dir
from esbonio.lsp.sphinx import get_src_dir
from esbonio.lsp.sphinx import SphinxConfig


@pytest.mark.parametrize(
    "setup, expected",
    [
        (
            ("/path/to/root", "/path/to/config"),
            pathlib.Path("/path/to/config"),
        ),
        (
            ("/path/to/root", "~/path/to/config"),
            pathlib.Path("~/path/to/config").expanduser(),
        ),
        (
            ("/path/to/root", "${workspaceRoot}/config"),
            pathlib.Path("/path/to/root/config").resolve(),
        ),
        (
            ("/path/to/root", "${workspaceRoot}/../config"),
            pathlib.Path("/path/to/config").resolve(),
        ),
        (
            ("/path/to/root", "${workspaceFolder}/config"),
            pathlib.Path("/path/to/root/config").resolve(),
        ),
        (
            ("/path/to/root", "${workspaceFolder}/../config"),
            pathlib.Path("/path/to/config").resolve(),
        ),
    ],
)
def test_expand_conf_dir(setup, expected):
    """Ensure that the ``expand_conf_dir`` function works as expected."""

    root_uri, conf_dir = setup

    actual = expand_conf_dir(root_uri, conf_dir)
    assert actual == expected


@pytest.mark.parametrize(
    "setup, expected",
    [
        (
            (
                "file:///path/to/root",
                pathlib.Path("/path/to/config"),
                SphinxConfig(srcDir="/path/to/src"),
            ),
            pathlib.Path("/path/to/src"),
        ),
        (
            (
                "file:///path/to/root",
                pathlib.Path("/path/to/config"),
                SphinxConfig(srcDir="~/path/to/src"),
            ),
            pathlib.Path("~/path/to/src").expanduser(),
        ),
        (
            (
                "file:///path/to/root",
                pathlib.Path("/path/to/config"),
                SphinxConfig(srcDir="${workspaceRoot}/src"),
            ),
            pathlib.Path("/path/to/root/src").resolve(),
        ),
        (
            (
                "file:///path/to/root",
                pathlib.Path("/path/to/config"),
                SphinxConfig(srcDir="${workspaceRoot}/../src"),
            ),
            pathlib.Path("/path/to/src").resolve(),
        ),
        (
            (
                "file:///path/to/root",
                pathlib.Path("/path/to/config"),
                SphinxConfig(srcDir="${workspaceFolder}/src"),
            ),
            pathlib.Path("/path/to/root/src").resolve(),
        ),
        (
            (
                "file:///path/to/root",
                pathlib.Path("/path/to/config"),
                SphinxConfig(srcDir="${workspaceFolder}/../src"),
            ),
            pathlib.Path("/path/to/src").resolve(),
        ),
        (
            (
                "file:///path/to/root",
                pathlib.Path("/path/to/config"),
                SphinxConfig(srcDir="${confDir}/src"),
            ),
            pathlib.Path("/path/to/config/src").resolve(),
        ),
        (
            (
                "file:///path/to/root",
                pathlib.Path("/path/to/config"),
                SphinxConfig(srcDir="${confDir}/../src"),
            ),
            pathlib.Path("/path/to/src").resolve(),
        ),
    ],
)
def test_get_src_dir(setup, expected):
    """Ensure that the ``get_src_dir`` function works as expected."""

    root_uri, conf_dir, sphinx_config = setup

    actual = get_src_dir(root_uri, conf_dir, sphinx_config)
    assert actual == expected


@pytest.mark.parametrize(
    "setup, expected",
    [
        (
            (
                "file:///path/to/root",
                pathlib.Path("/path/to/config"),
                SphinxConfig(buildDir="/path/to/build"),
            ),
            pathlib.Path("/path/to/build"),
        ),
        (
            (
                "file:///path/to/root",
                pathlib.Path("/path/to/config"),
                SphinxConfig(buildDir="~/path/to/build"),
            ),
            pathlib.Path("~/path/to/build").expanduser(),
        ),
        (
            (
                "file:///path/to/root",
                pathlib.Path("/path/to/config"),
                SphinxConfig(buildDir="${workspaceRoot}/build"),
            ),
            pathlib.Path("/path/to/root/build").resolve(),
        ),
        (
            (
                "file:///path/to/root",
                pathlib.Path("/path/to/config"),
                SphinxConfig(buildDir="${workspaceRoot}/../build"),
            ),
            pathlib.Path("/path/to/build").resolve(),
        ),
        (
            (
                "file:///path/to/root",
                pathlib.Path("/path/to/config"),
                SphinxConfig(buildDir="${workspaceFolder}/build"),
            ),
            pathlib.Path("/path/to/root/build").resolve(),
        ),
        (
            (
                "file:///path/to/root",
                pathlib.Path("/path/to/config"),
                SphinxConfig(buildDir="${workspaceFolder}/../build"),
            ),
            pathlib.Path("/path/to/build").resolve(),
        ),
        (
            (
                "file:///path/to/root",
                pathlib.Path("/path/to/config"),
                SphinxConfig(buildDir="${confDir}/build"),
            ),
            pathlib.Path("/path/to/config/build").resolve(),
        ),
        (
            (
                "file:///path/to/root",
                pathlib.Path("/path/to/config"),
                SphinxConfig(buildDir="${confDir}/../build"),
            ),
            pathlib.Path("/path/to/build").resolve(),
        ),
    ],
)
def test_get_build_dir(setup, expected):
    """Ensure that the ``get_build_dir`` function works as expected."""

    root_uri, conf_dir, sphinx_config = setup

    actual = get_build_dir(root_uri, conf_dir, sphinx_config)
    assert actual == expected
