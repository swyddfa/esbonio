from __future__ import annotations

import asyncio
import inspect
import logging
import traceback
import typing
from functools import partial

if typing.TYPE_CHECKING:
    from typing import Any


class EventSource:
    """Simple component for emitting events."""

    # TODO: It might be nice to do some fancy typing here so that type checkers
    # etc know which events are possible etc.

    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger(__name__)
        """The logging instance to use."""

        self.handlers: dict[str, set] = {}
        """Collection of handlers for various events."""

        self._tasks: set[asyncio.Task] = set()
        """Holds tasks that are currently executing an async event handler."""

    def add_listener(self, event: str, handler):
        """Add a listener for the given event name."""
        self.handlers.setdefault(event, set()).add(handler)

    def _finish_task(self, event: str, listener_name: str, task: asyncio.Task[Any]):
        """Cleanup a finished task."""
        self._tasks.discard(task)

        if (exc := task.exception()) is not None:
            self.logger.error(
                "Error in '%s' async handler '%s'\n%s",
                event,
                listener_name,
                "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
            )

    def trigger(self, event: str, *args, **kwargs):
        """Trigger the event with the given name."""

        for listener in self.handlers.get(event, set()):
            listener_name = f"{listener}"

            try:
                res = listener(*args, **kwargs)

                # Event listeners may be async
                if inspect.iscoroutine(res):
                    task = asyncio.create_task(res)
                    task.add_done_callback(
                        partial(self._finish_task, event, listener_name)
                    )

                    self._tasks.add(task)

            except Exception:
                self.logger.error(
                    "Error in '%s' handler '%s'", event, listener_name, exc_info=True
                )
