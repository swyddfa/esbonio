import pytest

from esbonio.lsp.roles import Roles
from esbonio.lsp.rst import RstLanguageServer
from esbonio.lsp.rst import _get_setup_arguments
from esbonio.lsp.sphinx import SphinxLanguageServer


def test_get_feature_by_string():
    """Ensure that a language feature can be retrieved by a string, but raises a
    deprecation warning."""

    rst = RstLanguageServer()
    expected = Roles(rst)

    rst.add_feature(expected)
    key = f"{expected.__module__}.{expected.__class__.__name__}"

    with pytest.deprecated_call():
        actual = rst.get_feature(key)

    assert actual is expected


def test_get_feature_by_cls():
    """Ensure that a language feature can be retrieved via its class definition."""

    rst = RstLanguageServer()
    expected = Roles(rst)

    rst.add_feature(expected)
    actual = rst.get_feature(Roles)

    assert actual is expected


def test_get_missing_feature_by_string():
    """Ensure that if a language feature is missing ``None`` is returned, but a
    deprecation warning is raised."""

    rst = RstLanguageServer()

    with pytest.deprecated_call():
        actual = rst.get_feature("xxx")

    assert actual is None


def test_get_missing_feature_by_cls():
    """Ensure that if a language feature is missing ``None`` is returned."""

    rst = RstLanguageServer()
    assert rst.get_feature(Roles) is None


def test_get_setup_arguments_rst_server():
    """Ensure that we can correctly construct the set of arguments to pass to a module's
    setup function."""

    def setup(rst: RstLanguageServer):
        ...

    server = RstLanguageServer()
    args = _get_setup_arguments(server, setup, "modname")

    assert args == {"rst": server}


def test_get_setup_arguments_server_superclass():
    """If the setup function is not compatible with the given server it should be
    skipped."""

    def setup(rst: SphinxLanguageServer):
        ...

    server = RstLanguageServer()
    args = _get_setup_arguments(server, setup, "modname")

    assert args is None


def test_get_setup_arguments_sphinx_server():
    """Ensure that we can correctly construct the set of arguments to pass to a module's
    setup function."""

    def setup(ls: SphinxLanguageServer):
        ...

    server = SphinxLanguageServer()
    args = _get_setup_arguments(server, setup, "modname")

    assert args == {"ls": server}


def test_get_setup_arguments_server_subclass():
    """Ensure that we can correctly construct the set of arguments to pass to a module's
    setup function."""

    def setup(ls: RstLanguageServer):
        ...

    server = SphinxLanguageServer()
    args = _get_setup_arguments(server, setup, "modname")

    assert args == {"ls": server}


def test_get_setup_arguments_server_and_feature():
    """We should also be able to automatically pass the correct language features"""

    def setup(rst: RstLanguageServer, rs: Roles):
        ...

    server = RstLanguageServer()

    roles = Roles(server)
    server.add_feature(roles)

    args = _get_setup_arguments(server, setup, "modname")

    assert args == {"rst": server, "rs": roles}


def test_get_setup_arguments_feature_only():
    """It should be possible to request just language features."""

    def setup(roles: Roles):
        ...

    server = RstLanguageServer()

    roles = Roles(server)
    server.add_feature(roles)

    args = _get_setup_arguments(server, setup, "modname")

    assert args == {"roles": roles}


def test_get_setup_arguments_missing_feature():
    """If a requested feature is not available the function should be skipped."""

    def setup(rst: RstLanguageServer, rs: Roles):
        ...

    server = RstLanguageServer()
    args = _get_setup_arguments(server, setup, "modname")

    assert args is None


def test_get_setup_arguments_wrong_type():
    """If an unsupported type is requested it should be skipped."""

    def setup(rst: RstLanguageServer, rs: int):
        ...

    server = RstLanguageServer()
    args = _get_setup_arguments(server, setup, "modname")

    assert args is None
