"""The dispatch log — the at-most-once boundary (**B2**).

A record of which ``(recipient, alert_id)`` pairs have already been delivered.
Delivery is at-least-once (a worker can crash or retry between "send" and
"ack"), so the *effect* is made at-most-once by consulting this log: deliver only
if this recipient hasn't already received this alert, then record it.

Keyed on the alert's **stable id** (born with the event), which is what makes it
survive retries and re-enqueues — a counter or attempt id would change on replay
and let the duplicate through.
"""

from __future__ import annotations


class DispatchLog:
    def __init__(self) -> None:
        self._seen: set[tuple[str, str]] = set()

    def was_dispatched(self, recipient_id: str, alert_id: str) -> bool:
        return (recipient_id, alert_id) in self._seen

    def mark(self, recipient_id: str, alert_id: str) -> None:
        self._seen.add((recipient_id, alert_id))

    def count(self) -> int:
        return len(self._seen)
