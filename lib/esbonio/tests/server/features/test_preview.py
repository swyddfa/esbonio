from __future__ import annotations

import pytest

from esbonio.server.features.preview_manager.preview import RequestHandler


@pytest.fixture
def handler() -> RequestHandler:
    """A ``RequestHandler`` instance without invoking ``__init__``.

    ``SimpleHTTPRequestHandler.__init__`` expects an active socket which we
    don't need for unit-testing ``guess_type``, so we construct via ``__new__``.
    """
    return RequestHandler.__new__(RequestHandler)


@pytest.mark.parametrize(
    "path,expected",
    [
        ("foo.html", "text/html; charset=utf-8"),
        ("foo.htm", "text/html; charset=utf-8"),
        ("foo.css", "text/css; charset=utf-8"),
        ("foo.txt", "text/plain; charset=utf-8"),
    ],
)
def test_text_mime_types_declare_utf8_charset(
    handler: RequestHandler, path: str, expected: str
):
    """Text responses should declare ``charset=utf-8`` so browsers don't fall
    back to a locale-dependent encoding when rendering UTF-8 content."""
    assert handler.guess_type(path) == expected


@pytest.mark.parametrize(
    "path",
    [
        "foo.png",
        "foo.jpg",
        "foo.svg",
        "foo.woff2",
        "foo.pdf",
    ],
)
def test_non_text_mime_types_unchanged(handler: RequestHandler, path: str):
    """Non-text MIME types should pass through without a charset suffix."""
    assert "charset=" not in handler.guess_type(path)
