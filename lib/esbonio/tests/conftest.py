import pathlib

import pytest

from esbonio.server import Uri

TEST_DIR = pathlib.Path(__file__).parent


@pytest.fixture(scope="session")
def uri_for():
    """Helper function for returning the uri for a given file in the ``tests/``
    directory."""

    def fn(*args):
        path = (TEST_DIR / pathlib.Path(*args)).resolve()
        assert path.exists(), f"{path} does not exist"
        return Uri.for_file(str(path))

    return fn
