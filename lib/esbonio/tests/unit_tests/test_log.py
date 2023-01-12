import logging
import sys

import pytest
from lsprotocol.types import DiagnosticSeverity
from lsprotocol.types import DiagnosticTag
from pygls import IS_WIN

from esbonio.lsp.log import LspHandler

if sys.version_info.minor < 8:
    from mock import Mock
else:
    from unittest.mock import Mock


@pytest.mark.parametrize(
    "message,expected",
    [
        (
            "/path/to/file.py:108: Warning: Here is a warning message",
            {
                "uri": "file:///path/to/file.py",
                "line": 108,
                "message": "Here is a warning message",
                "deprecated": False,
            },
        ),
        (
            "/path/to/file.py:18: DeprecationWarning: Here is a warning message",
            {
                "uri": "file:///path/to/file.py",
                "line": 18,
                "message": "Here is a warning message",
                "deprecated": True,
            },
        ),
        (
            "/path/to/file.py:xx: DeprecationWarning: Here is a warning message",
            {
                "uri": "file:///path/to/file.py",
                "line": 1,
                "message": "Here is a warning message",
                "deprecated": True,
            },
        ),
        pytest.param(
            "c:\\path\\to\\file.py:18: DeprecationWarning: Here is a warning message",
            {
                "uri": "file:///c:/path/to/file.py",
                "line": 18,
                "message": "Here is a warning message",
                "deprecated": True,
            },
            marks=pytest.mark.skipif(not IS_WIN, reason="test only valid on Windows"),
        ),
    ],
)
def test_handle_warning(message: str, expected: dict):
    """Ensure that we can parse warning messages correctly."""

    server = Mock()
    handler = LspHandler(server, True)

    record = logging.LogRecord(
        "testname",
        logging.WARNING,
        "/path/to/file.py",
        12,
        "%s",
        (message,),
        exc_info=None,
    )
    handler.handle_warning(record)

    namespace, uri, diagnostic = server.add_diagnostics.call_args.args

    assert namespace == "esbonio"
    assert uri == expected["uri"]

    assert diagnostic.message == expected["message"]
    assert diagnostic.severity == DiagnosticSeverity.Warning
    assert diagnostic.range.start.line == expected["line"] - 1
    assert diagnostic.range.end.line == expected["line"]

    if expected["deprecated"]:
        assert diagnostic.tags == [DiagnosticTag.Deprecated]
