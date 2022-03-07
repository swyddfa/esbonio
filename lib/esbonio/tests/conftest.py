import asyncio
import pathlib

import py.test
import pygls.uris as uri
from sphinx.application import Sphinx

from esbonio.lsp import create_language_server
from esbonio.lsp.sphinx import DEFAULT_MODULES
from esbonio.lsp.sphinx import SphinxLanguageServer
from esbonio.lsp.testing import ClientServer

# import logging
# from typing import Optional, Tuple

# Log everything in the test run to a file.
# log_file = pathlib.Path(__file__).parent / "test.log"
# logging.basicConfig(
#     level=logging.DEBUG,
#     filename=log_file,
#     filemode="w",
#     format="[%(asctime)s][%(threadName)s][%(levelname)s][%(name)s]: %(message)s",
# )
# logger = logging.getLogger("testsuite")


# def pytest_runtest_logstart(
#     nodeid: str, location: Tuple[str, Optional[int], str]
# ) -> None:
#     """Called at the start of each test."""
#     title = f" Start Test: {nodeid} "
#     logger.info(title.center(240, "-"))


# def pytest_runtest_logfinish(
#     nodeid: str, location: Tuple[str, Optional[int], str]
# ) -> None:
#     """Called at the end of each test"""
#     title = f" End Test: {nodeid} "
#     logger.info(title.center(240, "-"))


@py.test.fixture(scope="session")
def testdata():
    """Given the name of a file in the data/ folder and return its contents.

    Alternatively if the :code:`path_only` option is set just return the path to the
    file.
    """
    basepath = pathlib.Path(__file__).parent / "data"

    def loader(filename, path_only=False):
        filepath = basepath / filename

        if path_only:
            return filepath

        with filepath.open("rb") as f:
            return f.read()

    return loader


@py.test.fixture(scope="session")
def sphinx():
    """Return a Sphinx application instance pointed at the given project."""

    # Since extensions like intersphinx need to hit the network, let's cache
    # app instances so we only incur this cost once.
    cache = {}
    basepath = pathlib.Path(__file__).parent / "data"

    def loader(project):
        src = str(basepath / project)

        if src in cache:
            return cache[src]

        build = str(basepath / project / "_build")

        app = Sphinx(src, src, build, build, "html", status=None, warning=None)
        app.builder.read()

        cache[src] = app
        return cache[src]

    return loader


@py.test.fixture(scope="session")
def event_loop(request):
    # We need to redefine the event_loop fixture to match the scope of our
    # client_server fixture.
    #
    # https://github.com/pytest-dev/pytest-asyncio/issues/68#issuecomment-334083751

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@py.test.fixture(scope="session")
async def client_server():
    """Return a ClientServer instance for the given project."""

    # We only want one instance per configuration, so let's cache instances.
    cache = {}
    basepath = pathlib.Path(__file__).parent / "data"

    async def loader(project):
        fspath = str(basepath / project)
        root_uri = uri.from_fs_path(fspath)

        if root_uri in cache:
            return cache[root_uri]

        loop = asyncio.new_event_loop()
        server = create_language_server(
            SphinxLanguageServer, DEFAULT_MODULES, loop=loop
        )
        client_server = ClientServer(server)
        await client_server.start(root_uri)

        cache[root_uri] = client_server
        return cache[root_uri]

    yield loader

    # Session cleanup
    for v in cache.values():
        await v.stop()
