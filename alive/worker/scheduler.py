"""Scheduled sweeps on the injected clock.

A real deployment rescoring continuously would also run a periodic sweep —
recompute every member, re-evaluate alerts — to catch members whose risk drifted
without a new reading arriving, and to retry anything that failed to dispatch.
Here it's a plain method the tests call deterministically; there's no real timer,
so nothing sleeps.
"""

from __future__ import annotations

from ..core.clock import Clock
from ..store.member_store import MemberStore
from .processor import Processor


class Scheduler:
    def __init__(self, processor: Processor, members: MemberStore, clock: Clock) -> None:
        self._processor = processor
        self._members = members
        self._clock = clock
        self._last_sweep: float | None = None

    def sweep(self) -> int:
        """Recompute and re-evaluate every member. Returns the count rescored."""
        n = 0
        for member in self._members.members():
            if self._processor.rescore(member.member_id) is not None:
                n += 1
        self._last_sweep = self._clock.now()
        return n

    @property
    def last_sweep(self) -> float | None:
        return self._last_sweep
