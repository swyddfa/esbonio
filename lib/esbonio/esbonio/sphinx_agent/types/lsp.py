from __future__ import annotations

import enum
from dataclasses import dataclass


@dataclass(frozen=True)
class Position:
    line: int
    character: int


@dataclass(frozen=True)
class Range:
    start: Position
    end: Position


@dataclass(frozen=True)
class Location:
    uri: str
    range: Range


class DiagnosticSeverity(enum.IntEnum):
    Error = 1
    Warning = 2
    Information = 3
    Hint = 4


@dataclass(frozen=True)
class Diagnostic:
    range: Range
    message: str
    severity: DiagnosticSeverity
