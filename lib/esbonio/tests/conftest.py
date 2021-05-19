import pathlib

import py.test
from sphinx.application import Sphinx


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
