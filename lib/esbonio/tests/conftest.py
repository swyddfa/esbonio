import asyncio
import pathlib

import pygls.uris as Uri
import pytest

TEST_DIR = pathlib.Path(__file__).parent


@pytest.fixture(scope="session")
def uri_for():
    """Helper function for returning the uri for a given file in the ``tests/``
    directory."""

    def fn(*args):
        path = (TEST_DIR / pathlib.Path(*args)).resolve()
        assert path.exists()

        uri = Uri.from_fs_path(str(path))
        assert uri is not None

        return uri

    return fn


@pytest.fixture(scope="session")
def event_loop():
    # We need to redefine the event_loop fixture to match the scope of our
    # client_server fixture.
    #
    # https://github.com/pytest-dev/pytest-asyncio/issues/68#issuecomment-334083751

    loop = asyncio.get_event_loop_policy().new_event_loop()
    asyncio.set_event_loop(loop)

    yield loop

    loop.close()
