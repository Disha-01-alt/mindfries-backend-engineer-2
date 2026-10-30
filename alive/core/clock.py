"""The clock the engine reads *processing time* from.

Crucial distinction this whole codebase turns on:

  * **event time** — when a reading actually happened on the device. It lives on
    the Sample (`Sample.event_time`) and is the only time that affects a score.
  * **processing time** — when the engine got around to handling it. That is
    what this clock reports, and it is used only for operational concerns:
    retry backoff, outbox timestamps, "when did we last sweep".

Production uses :class:`SystemClock`; tests use :class:`ManualClock` so every
TTL, watermark delay and sweep is a controllable input rather than a real wait.
A score must never depend on which clock is installed — if it does, that's a bug.
"""

from __future__ import annotations

import time
from typing import Protocol


class Clock(Protocol):
    def now(self) -> float:  # epoch seconds
        ...


class SystemClock:
    """Reads real wall-clock time. The only place in the engine that does."""

    def now(self) -> float:
        return time.time()


class ManualClock:
    """A clock the caller controls. ``advance`` moves it forward; nothing else does."""

    def __init__(self, start: float = 0.0) -> None:
        self._t = float(start)

    def now(self) -> float:
        return self._t

    def advance(self, seconds: float) -> float:
        if seconds < 0:
            raise ValueError("time only moves forward")
        self._t += seconds
        return self._t
