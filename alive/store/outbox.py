"""The outbox — pending alerts and recommendations awaiting delivery.

Alerting enqueues here; the worker drains and dispatches. Modelling it as an
outbox (rather than delivering inline) is the real pattern — the business write
and the intent-to-notify are decoupled, and the worker provides the retry loop.
That decoupling is also what makes duplicate delivery *possible* (a redelivery on
retry), which is exactly why dispatch has to be idempotent.
"""

from __future__ import annotations

from collections import deque
from typing import Union

from ..core.events import Alert, Recommendation

Item = Union[Alert, Recommendation]


class Outbox:
    def __init__(self) -> None:
        self._pending: deque[Item] = deque()

    def enqueue(self, item: Item) -> None:
        self._pending.append(item)

    def drain(self) -> list[Item]:
        """Remove and return everything currently pending, in FIFO order."""
        out = list(self._pending)
        self._pending.clear()
        return out

    def peek(self) -> list[Item]:
        return list(self._pending)

    def __len__(self) -> int:
        return len(self._pending)
