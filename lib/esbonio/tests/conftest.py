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


@pytest.fixture(scope="session")
def uri_for():
    """Helper function for returning the uri for a given file in the ``tests/``
    directory."""

    def fn(*args):
        path = (TEST_DIR / pathlib.Path(*args)).resolve()
        assert path.exists(), f"{path} does not exist"
        return Uri.for_file(str(path))

    return fn
