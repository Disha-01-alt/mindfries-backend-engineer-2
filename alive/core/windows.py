"""Tumbling time-window attribution.

Scoring aggregates samples over fixed windows (a day, an hour). The invariant
(**B4**) is that **each event belongs to exactly one window** — never counted
twice, never dropped at a boundary. Tumbling windows give that by construction
*only if* boundary ownership is consistent, so every function here uses a
**half-open** interval ``[start, end)``: a sample whose ``event_time`` falls
exactly on a boundary belongs to the window that *starts* there, not the one
that ends there.

Windows are anchored to an epoch (default 0), so window boundaries are a pure
function of ``event_time`` and ``length`` — independent of when the engine runs.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

DAY = 86_400.0
HOUR = 3_600.0


@dataclass(frozen=True)
class Window:
    start: float
    end: float

    def __post_init__(self) -> None:
        if self.end <= self.start:
            raise ValueError("window end must be after start")

    @property
    def length(self) -> float:
        return self.end - self.start

    def contains(self, event_time: float) -> bool:
        """Half-open membership: start <= t < end."""
        return self.start <= event_time < self.end


def window_start(event_time: float, length: float = DAY, anchor: float = 0.0) -> float:
    if length <= 0:
        raise ValueError("window length must be positive")
    n = math.floor((event_time - anchor) / length)
    return anchor + n * length


def window_for(event_time: float, length: float = DAY, anchor: float = 0.0) -> Window:
    s = window_start(event_time, length, anchor)
    return Window(s, s + length)


def windows_covering(start: float, end: float, length: float = DAY, anchor: float = 0.0) -> list[Window]:
    """Every window that overlaps the half-open range ``[start, end)``, in order."""
    if end <= start:
        return []
    first = window_start(start, length, anchor)
    out: list[Window] = []
    s = first
    while s < end:
        out.append(Window(s, s + length))
        s += length
    return out
