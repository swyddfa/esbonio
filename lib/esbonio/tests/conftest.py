import pathlib

import pytest

from esbonio.server import Uri

TEST_DIR = pathlib.Path(__file__).parent


def pytest_addoption(parser):
    """Add additional cli arguments to pytest."""

    group = parser.getgroup("esbonio")
    group.addoption(
        "--enable-devtools",
        dest="enable_devtools",
        action="store_true",
        help="enable lsp-devtools integrations",
    )


@pytest.hookimpl(tryfirst=True)
def pytest_report_header(config: pytest.Config):
    """Report additional information in pytest's output header"""
    lines = []

    try:
        from sphinx import __version__

        lines.append(f"sphinx: v{__version__}")
    except ImportError:
        lines.append("sphinx: none")

    return lines


@pytest.fixture(scope="session")
def uri_for():
    """Helper function for returning the uri for a given file in the ``tests/``
    directory."""

    def fn(*args):
        path = (TEST_DIR / pathlib.Path(*args)).resolve()
        assert path.exists(), f"{path} does not exist"
        return Uri.for_file(str(path))

    return fn
