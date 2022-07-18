import inspect
import logging
import traceback
from typing import Optional

import pygls.uris as Uri
from pygls.lsp.types import Location
from pygls.lsp.types import Position
from pygls.lsp.types import Range


def get_object_location(obj: object, logger: logging.Logger) -> Optional[Location]:
    """Given an object, attempt to find the location of its implementation.

    Parameters
    ----------
    obj
       The object to find the implementation of

    logger
       A logger object
    """

    try:
        file = inspect.getsourcefile(obj)  # type: ignore
        if file is None:
            return None

        source, line = inspect.getsourcelines(obj)  # type: ignore
        return Location(
            uri=Uri.from_fs_path(file),
            range=Range(
                start=Position(line=line - 1, character=0),
                end=Position(line=line + len(source), character=0),
            ),
        )

    except Exception:
        logger.debug(
            "Unable to get implementation location\n%s", traceback.format_exc()
        )
        return None
