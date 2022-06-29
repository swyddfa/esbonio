import pytest

from esbonio.lsp.roles import Roles
from esbonio.lsp.rst import RstLanguageServer


@pytest.mark.filterwarnings("ignore:There is no current event loop")
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


@pytest.mark.filterwarnings("ignore:There is no current event loop")
def test_get_feature_by_cls():
    """Ensure that a language feature can be retrieved via its class definition."""

    rst = RstLanguageServer()
    expected = Roles(rst)

    rst.add_feature(expected)
    actual = rst.get_feature(Roles)

    assert actual is expected


@pytest.mark.filterwarnings("ignore:There is no current event loop")
def test_get_missing_feature_by_string():
    """Ensure that if a language feature is missing ``None`` is returned, but a
    deprecation warning is raised."""

    rst = RstLanguageServer()

    with pytest.deprecated_call():
        actual = rst.get_feature("xxx")

    assert actual is None


@pytest.mark.filterwarnings("ignore:There is no current event loop")
def test_get_missing_feature_by_cls():
    """Ensure that if a language feature is missing ``None`` is returned."""

    rst = RstLanguageServer()
    assert rst.get_feature(Roles) is None
