import functools
import logging
from types import TracebackType
from typing import Any
from typing import Callable
from typing import Iterable
from typing import Iterator
from typing import Optional
from typing import Type
from typing import TypeVar

from . import types
from .util import send_message

T = TypeVar("T")


def patch_sphinx():
    """Monkey patch parts of Sphinx with our own implementations."""
    try:
        from sphinx.util import display
    except ImportError:
        # display submodule was not introduced until Sphinx 6.x
        import sphinx.util as display  # type: ignore[no-redef]

    display.status_iterator = status_iterator
    display.progress_message = progress_message  # type: ignore


def status_iterator(
    iterable: Iterable[T],
    summary: str,
    color: str = "",
    length: int = 0,
    verbosity: int = 0,
    stringify_func: Optional[Callable[[Any], str]] = None,
) -> Iterator[T]:
    """Used to override Sphinx's version of this function.
    Sends progress reports to the client as well as the usual logs.
    """
    from sphinx.util.logging import NAMESPACE

    try:
        from sphinx.util.display import display_chunk
    except ImportError:
        # display submodule was not introduced until Sphinx 5.x
        from sphinx.util import display_chunk  # type: ignore[no-redef]

    if stringify_func is None:
        stringify_func = display_chunk

    logger = logging.getLogger(NAMESPACE)
    send_message(types.ProgressMessage(params=types.ProgressParams(message=summary)))

    if verbosity == 0:
        logger.info(summary)

    percentage = " "
    for i, item in enumerate(iterable, start=1):
        if verbosity > 0:
            if length > 0:
                percentage = f" [{int((i / length) * 100): >3d}%] "
            logger.info(f"{summary}{percentage}{stringify_func(item)}")

        yield item


class progress_message:
    """Used to override Spinx's version of this, reports progress to the client."""

    def __init__(self, message: str, *, nonl: bool = True) -> None:
        self.message = message

    def __enter__(self) -> None:
        send_message(
            types.ProgressMessage(params=types.ProgressParams(message=self.message))
        )

    def __exit__(
        self,
        typ: Optional[Type[BaseException]],
        val: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> bool:
        from sphinx.locale import __
        from sphinx.util.logging import NAMESPACE

        try:
            from sphinx.util import display
        except ImportError:
            # display submodule was not introduced until Sphinx 6.x
            import sphinx.util as display  # type: ignore[no-redef]

        logger = logging.getLogger(NAMESPACE)

        if isinstance(val, display.SkipProgressMessage):
            logger.info(self.message + "... " + __("skipped"))
            if val.args:
                logger.info(*val.args)
            return True
        elif val:
            logger.info(__(self.message + "... " + "failed"))
        else:
            logger.info(self.message + "... " + __("done"))

        return False

    def __call__(self, f: Callable) -> Callable:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with self:
                return f(*args, **kwargs)

        return wrapper
