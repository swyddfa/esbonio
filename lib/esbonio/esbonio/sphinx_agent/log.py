import inspect
import logging
import os
import pathlib
import sys
from types import ModuleType
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Union

from sphinx.util.logging import OnceFilter
from sphinx.util.logging import SphinxLogRecord
from sphinx.util.logging import WarningLogRecordTranslator

from . import types
from .util import logger
from .util import send_message

DIAGNOSTIC_SEVERITY = {
    logging.ERROR: types.DiagnosticSeverity.Error,
    logging.INFO: types.DiagnosticSeverity.Information,
    logging.WARNING: types.DiagnosticSeverity.Warning,
}


class SphinxLogHandler(logging.Handler):
    """A logging handler that can extract errors from Sphinx's build output."""

    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.app = app
        self.translator = WarningLogRecordTranslator(app)
        self.only_once = OnceFilter()
        self.diagnostics: Dict[str, Set[types.Diagnostic]] = {}

    def get_location(self, location: str) -> Tuple[str, Optional[int]]:
        if not location:
            conf = pathlib.Path(self.app.confdir, "conf.py")
            return (str(conf), None)

        lineno = None
        path, parts = self.get_location_path(location)

        if len(parts) == 1:
            try:
                lineno = int(parts[0])
            except ValueError:
                pass

        if len(parts) == 2 and parts[0].startswith("docstring of "):
            target = parts[0].replace("docstring of ", "")
            lineno = self.get_docstring_location(target, parts[1])

        return (path, lineno)

    def get_location_path(self, location: str) -> Tuple[str, List[str]]:
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

    def get_docstring_location(self, target: str, offset: str) -> Optional[int]:
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

    def emit(self, record: logging.LogRecord) -> None:
        conditions = [
            "sphinx" not in record.name,
            record.levelno not in {logging.WARNING, logging.ERROR},
        ]

        if any(conditions):
            # Log the record as normal
            self.do_emit(record)
            return

        # Let sphinx extract location info for warning/error messages
        self.translator.filter(record)  # type: ignore

        # Only process errors/warnings once.
        # Note: This isn't a silver bullet as it only catches messages that are explicitly
        #       marked as to be logged only once e.g. logger.warning(..., once=True).
        if not self.only_once.filter(record):
            return

        loc = record.location if isinstance(record, SphinxLogRecord) else ""
        doc, lineno = self.get_location(loc)
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

        self.diagnostics.setdefault(doc, set()).add(diagnostic)
        self.do_emit(record)

    def do_emit(self, record):
        params = types.LogMessageParams(message=self.format(record).strip(), type=4)
        send_message(types.LogMessage(params=params))
