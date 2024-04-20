"""Helpers and utilities for writing tests."""

from lsprotocol import types


def range_from_str(spec: str) -> types.Range:
    """Create a range from the given string ``a:b-x:y``"""
    start, end = spec.split("-")
    sl, sc = start.split(":")
    el, ec = end.split(":")

    return types.Range(
        start=types.Position(line=int(sl), character=int(sc)),
        end=types.Position(line=int(el), character=int(ec)),
    )
