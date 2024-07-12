from __future__ import annotations

import inspect
import logging
import os
import pathlib
import sys
import typing

from . import types
from .types import Uri
from .util import logger

if typing.TYPE_CHECKING:
    from types import ModuleType
    from typing import Any
    from typing import Dict
    from typing import List
    from typing import Optional
    from typing import Set
    from typing import Tuple
    from typing import Union


DIAGNOSTIC_SEVERITY = {
    logging.ERROR: types.DiagnosticSeverity.Error,
    logging.INFO: types.DiagnosticSeverity.Information,
    logging.WARNING: types.DiagnosticSeverity.Warning,
}


class DiagnosticFilter(logging.Filter):
    """A logging handler that can extract errors from Sphinx's build output."""

    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.app = app
        self.diagnostics: Dict[Uri, Set[types.Diagnostic]] = {}

    def filter(self, record: logging.LogRecord) -> bool:
        conditions = [
            "sphinx" not in record.name,
            record.levelno not in {logging.WARNING, logging.ERROR},
        ]

        if any(conditions):
            return True

        loc = getattr(record, "location", "")
        uri, lineno = source_to_uri_and_linum(loc)

        if uri is None:
            conf = pathlib.Path(self.app.confdir, "conf.py")
            uri, lineno = (Uri.for_file(conf), None)

        line = lineno or 1

        try:
            # Not every message contains a string...
            if not isinstance(record.msg, str):
                message = str(record.msg)
            else:
                message = record.msg

            # Only attempt to format args if there are args to format
            if record.args is not None and len(record.args) > 0:
                message = message % record.args

        except Exception:
            message = str(record.msg)
            logger.error("Unable to format diagnostic message: %s", exc_info=True)

        diagnostic = types.Diagnostic(
            range=types.Range(
                start=types.Position(line=line - 1, character=0),
                end=types.Position(line=line, character=0),
            ),
            message=message,
            severity=DIAGNOSTIC_SEVERITY.get(
                record.levelno, types.DiagnosticSeverity.Warning
            ),
        )

        self.diagnostics.setdefault(uri, set()).add(diagnostic)
        return True


def source_to_uri_and_linum(
    location: Optional[str],
) -> Tuple[Optional[Uri], Optional[int]]:
    """Convert the given source location to a uri and corresponding line number

    Parameters
    ----------
    location
       The location to convert

    Returns
    -------
    Tuple[Optional[Uri], Optional[int]]
       The corresponding uri and line number, if known
    """
    if location is None:
        return None, None

    lineno = None
    path, parts = _get_location_path(location)

    if len(parts) == 1:
        try:
            lineno = int(parts[0])
        except ValueError:
            pass

    if len(parts) == 2 and parts[0].startswith("docstring of "):
        target = parts[0].replace("docstring of ", "")
        lineno = _get_docstring_linum(target, parts[1])

    return Uri.for_file(path), lineno


def _get_location_path(location: str) -> Tuple[str, List[str]]:
    """Determine the filepath from the given location."""

    if location.startswith("internal padding before "):
        location = location.replace("internal padding before ", "")

    if location.startswith("internal padding after "):
        location = location.replace("internal padding after ", "")

    path, *parts = location.split(":")

    # On windows the rest of the path will be the first element of parts
    if pathlib.Path(location).drive:
        path += f":{parts.pop(0)}"

    # Diagnostics in .. included:: files are reported relative to the process'
    # working directory, so ensure the path is absolute.
    path = os.path.abspath(path)

    return path, parts


def _get_docstring_linum(target: str, offset: str) -> Optional[int]:
    # The containing module will be the longest substring we can find in target
    candidates = [m for m in sys.modules.keys() if target.startswith(m)] + [""]
    module = sys.modules.get(sorted(candidates, key=len, reverse=True)[0], None)

    if module is None:
        return None

    obj: Union[ModuleType, Any, None] = module
    dotted_name = target.replace(module.__name__ + ".", "")

    for name in dotted_name.split("."):
        obj = getattr(obj, name, None)
        if obj is None:
            return None

    try:
        _, line = inspect.getsourcelines(obj)  # type: ignore

        # Correct off by one error for docstrings that don't start with a newline.
        nl = (obj.__doc__ or "").startswith("\n")
        return line + int(offset) - (not nl)
    except Exception:
        logger.debug("Unable to determine diagnostic location\n%s", exc_info=True)
        return None
