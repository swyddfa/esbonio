import asyncio
import os
import pathlib
import threading
import unittest.mock as mock

import py.test

from docutils.io import StringInput
from docutils.parsers.rst import Parser, directives
from docutils.readers.standalone import Reader

from pygls.features import EXIT, SHUTDOWN
from pygls.server import LanguageServer

from sphinx.application import Sphinx
from sphinx.ext.doctest import DoctestDirective

from esbonio.lsp import BUILTIN_MODULES, create_language_server


@py.test.fixture(scope="session")
def client_server():
    """A fixture that sets up an LSP server + client.

    Originally based on https://github.com/openlawlibrary/pygls/blob/59f3056baa4de4c4fb374d3657194f2669c174bc/tests/conftest.py  # noqa: E501
    """

    # Pipes so that client + server can communicate
    csr, csw = os.pipe()
    scr, scw = os.pipe()

    # Server setup
    server = create_language_server(BUILTIN_MODULES)
    server_thread = threading.Thread(
        name="ServThread",
        target=server.start_io,
        args=(os.fdopen(csr, "rb"), os.fdopen(scw, "wb")),
    )

    server_thread.daemon = True
    server_thread.start()

    # Not entirely sure what this step does...
    server.thread_id = server_thread.ident

    # Client setup - we can get away with a vanilla 'LanguageServer' for this
    client = LanguageServer(asyncio.new_event_loop())
    client_thread = threading.Thread(
        name="ClntThread",
        target=client.start_io,
        args=(os.fdopen(scr, "rb"), os.fdopen(csw, "wb")),
    )

    client_thread.daemon = True
    client_thread.start()

    yield client, server

    response = client.lsp.send_request(SHUTDOWN).result(timeout=2)
    assert response is None
    client.lsp.notify(EXIT)


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
