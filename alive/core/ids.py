"""Stable, content-derived identifiers.

Idempotency and deduplication both hinge on an id that is *born with the data*
and identical across every retry and re-sync — never an arrival-order counter or
an attempt id (those change on replay, which is exactly how duplicates slip
through; see ``store/dispatch_log.py``).

``stable_id`` is a deterministic hash of its parts, so the same logical thing
always hashes to the same id regardless of when or how often it's computed.
"""

from __future__ import annotations

import hashlib
from typing import Any


def stable_id(*parts: Any, prefix: str = "") -> str:
    """A short, deterministic id derived from ``parts``.

    Order-sensitive on purpose: ``stable_id("a", "b") != stable_id("b", "a")``.
    ``None`` and numbers are stringified; floats are rounded to microseconds so a
    re-sync of the same instant doesn't produce a different id through FP noise.
    """
    canon = []
    for p in parts:
        if isinstance(p, float):
            canon.append(format(round(p, 6), ".6f"))
        else:
            canon.append(str(p))
    digest = hashlib.sha256("\x1f".join(canon).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}{digest}" if prefix else digest
