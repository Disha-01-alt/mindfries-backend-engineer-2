"""Dispatch — deliver an outbox item to its recipient.

Delivery is at-least-once: the worker can reprocess the outbox after a retry, and
alerting can re-emit the same alert on the next tick for the same window. So a
given alert may be handed to ``dispatch`` more than once.

NOTE: this baseline delivers every time it's called — it does **not** yet dedupe,
so a member or coach can receive the same alert twice. Making delivery
at-most-once per ``(recipient, alert-id)`` using the dispatch log is the
extension task; the stable ids and the ``DispatchLog`` are already in place.
"""

from __future__ import annotations

from ..core.events import Alert, Recommendation
from ..store.dispatch_log import DispatchLog
from ..store.outbox import Item


def _dedup_key(item: Item) -> tuple[str, str]:
    """(recipient, stable-id) — what at-most-once would be keyed on."""
    if isinstance(item, Alert):
        return item.dedup_key
    if isinstance(item, Recommendation):
        return (item.member_id, item.rec_id)
    raise TypeError(f"cannot dispatch {type(item).__name__}")


class Dispatcher:
    def __init__(self, dispatch_log: DispatchLog) -> None:
        self._log = dispatch_log
        self.deliveries: list[Item] = []  # the "sent" sink — what a recipient actually received

    def dispatch(self, item: Item) -> bool:
        """Deliver ``item``. Returns True if it went out, False if suppressed.

        Baseline: always delivers (at-least-once, duplicates possible).
        """
        self.deliveries.append(item)
        return True
