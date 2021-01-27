import asyncio
import logging
import os
import pathlib
import threading
import time
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
from esbonio.tutorial import SolutionDirective, TutorialDirective


@py.test.fixture(scope="session")
def client_server():
    """A fixture that sets up an LSP server + client.

    Originally based on https://github.com/openlawlibrary/pygls/blob/59f3056baa4de4c4fb374d3657194f2669c174bc/tests/conftest.py
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

    basepath = pathlib.Path(__file__).parent / "data"

    def loader(project):
        src = str(basepath / project)
        build = str(basepath / project / "_build")

        return Sphinx(src, src, build, build, "html", status=None, warning=None)

    return loader


@py.test.fixture(scope="session")
def rst_mock_settings():
    """Return a mock that can pretend to be the settings object needed to parse rst
    sources.

    It's not cleat what these settings should be, but it appears to be enough to get the
    tests to run.
    """
    settings = mock.Mock()

    # The following settings were obtained by running the following code and inspecting
    # the resulting settings object, so their values should be fairly sensible
    #
    # >>> from docutils.core import Publisher
    #
    # >>> publisher = Publisher()
    # >>> opts = publisher.setup_option_parser()
    # >>> settings = opts.get_default_values()

    settings.halt_level = 4
    settings.id_prefix = ""
    settings.language_code = "en"
    settings.report_level = 2

    # I'm assuming these settings are extras introduced by Sphinx since they were not
    # created as part of the defaults. I haven't currently tracked down the source of
    # truth of these so there's a good chance these values are **not** representative.

    settings.tab_width = 2

    # Fake some additional settings on the (Sphinx?) application object
    settings.env.app.confdir = "/project/docs"

    return settings


@py.test.fixture(scope="session")
def parse_rst(rst_mock_settings):
    """A fixture that attempts to produce a doctree from rst source in a representative
    environment."""

    # Register any extended directives with docutils
    directives.register_directive("doctest", DoctestDirective)
    directives.register_directive(SolutionDirective.NAME, SolutionDirective)
    directives.register_directive(TutorialDirective.NAME, TutorialDirective)

    def parse(src):
        parser = Parser()
        settings = rst_mock_settings

        reader = Reader()
        return reader.read(StringInput(src), parser, settings)

    return parse
