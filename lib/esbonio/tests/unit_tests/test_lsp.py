import pytest

from esbonio.lsp import _get_setup_arguments
from esbonio.lsp.roles import Roles
from esbonio.lsp.rst import RstLanguageServer
from esbonio.lsp.sphinx import SphinxLanguageServer


@pytest.mark.filterwarnings("ignore:There is no current event loop")
def test_get_setup_arguments_rst_server():
    """Ensure that we can correctly construct the set of arguments to pass to a module's
    setup function."""

    def setup(rst: RstLanguageServer):
        ...

    server = RstLanguageServer()
    args = _get_setup_arguments(server, setup, "modname")

    assert args == {"rst": server}


@pytest.mark.filterwarnings("ignore:There is no current event loop")
def test_get_setup_arguments_server_superclass():
    """If the setup function is not compatible with the given server it should be
    skipped."""

    def setup(rst: SphinxLanguageServer):
        ...

    server = RstLanguageServer()
    args = _get_setup_arguments(server, setup, "modname")

    assert args is None


@pytest.mark.filterwarnings("ignore:There is no current event loop")
def test_get_setup_arguments_sphinx_server():
    """Ensure that we can correctly construct the set of arguments to pass to a module's
    setup function."""

    def setup(ls: SphinxLanguageServer):
        ...

    server = SphinxLanguageServer()
    args = _get_setup_arguments(server, setup, "modname")

    assert args == {"ls": server}


@pytest.mark.filterwarnings("ignore:There is no current event loop")
def test_get_setup_arguments_server_subclass():
    """Ensure that we can correctly construct the set of arguments to pass to a module's
    setup function."""

    def setup(ls: RstLanguageServer):
        ...

    server = SphinxLanguageServer()
    args = _get_setup_arguments(server, setup, "modname")

    assert args == {"ls": server}


@pytest.mark.filterwarnings("ignore:There is no current event loop")
def test_get_setup_arguments_server_and_feature():
    """We should also be able to automatically pass the correct language features"""

    def setup(rst: RstLanguageServer, rs: Roles):
        ...

    server = RstLanguageServer()

    roles = Roles(server)
    server.add_feature(roles)

    args = _get_setup_arguments(server, setup, "modname")

    assert args == {"rst": server, "rs": roles}


@pytest.mark.filterwarnings("ignore:There is no current event loop")
def test_get_setup_arguments_feature_only():
    """It should be possible to request just language features."""

    def setup(roles: Roles):
        ...

    server = RstLanguageServer()

    roles = Roles(server)
    server.add_feature(roles)

    args = _get_setup_arguments(server, setup, "modname")

    assert args == {"roles": roles}


@pytest.mark.filterwarnings("ignore:There is no current event loop")
def test_get_setup_arguments_missing_feature():
    """If a requested feature is not available the function should be skipped."""

    def setup(rst: RstLanguageServer, rs: Roles):
        ...

    server = RstLanguageServer()
    args = _get_setup_arguments(server, setup, "modname")

    assert args is None


@pytest.mark.filterwarnings("ignore:There is no current event loop")
def test_get_setup_arguments_wrong_type():
    """If an unsupported type is requested it should be skipped."""

    def setup(rst: RstLanguageServer, rs: int):
        ...

    server = RstLanguageServer()
    args = _get_setup_arguments(server, setup, "modname")

    assert args is None
