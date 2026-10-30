"""Engine wiring for the API.

One process-wide engine, seeded with the demo population on first access so the
API has something to serve immediately. Tests build their own engine with a
ManualClock instead of using this one.
"""

from __future__ import annotations

from ..engine import Engine
from ..seed import seed

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = Engine()
        seed(_engine)
    return _engine


def reset_engine() -> None:
    global _engine
    _engine = None
