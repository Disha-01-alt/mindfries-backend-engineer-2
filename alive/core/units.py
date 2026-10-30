"""Unit normalization at the edge.

A reading can arrive in whatever unit its source speaks — a US glucometer in
mg/dL, a European one in mmol/L; a scale in kg or lb. Before anything is stored
or scored it is converted to the metric's single canonical unit (see
``metrics.py``). A unit we can't convert for that metric is rejected
(``UnitMismatchError``) rather than silently scored — a glucose value read as
mmol/L but treated as mg/dL would move a member's risk for no real reason.

This is invariant **B6**: every stored sample is in canonical units.
"""

from __future__ import annotations

from .errors import UnitMismatchError
from .metrics import MetricKind, canonical_unit

# Linear conversions INTO the canonical unit: canonical = value * factor + offset.
# Keyed by (from_unit, canonical_unit). Aliases map common spellings to one key.
_ALIASES = {
    "beats/min": "bpm",
    "bpm": "bpm",
    "ms": "ms",
    "millisecond": "ms",
    "msec": "ms",
    "s": "s",
    "sec": "s",
    "second": "s",
    "count": "count",
    "steps": "count",
    "min": "min",
    "minute": "min",
    "mins": "min",
    "h": "h",
    "hour": "h",
    "hr": "h",
    "%": "pct",
    "pct": "pct",
    "percent": "pct",
    "mg/dl": "mg/dL",
    "mg/dL": "mg/dL",
    "mmol/l": "mmol/L",
    "mmol/L": "mmol/L",
    "mmhg": "mmHg",
    "mmHg": "mmHg",
    "kg": "kg",
    "kilogram": "kg",
    "lb": "lb",
    "lbs": "lb",
    "pound": "lb",
    "degc": "degC",
    "degC": "degC",
    "c": "degC",
    "celsius": "degC",
    "degf": "degF",
    "degF": "degF",
    "f": "degF",
    "fahrenheit": "degF",
    "kcal": "kcal",
    "cal": "kcal",
    "kj": "kJ",
    "kJ": "kJ",
}

# (normalized_from_unit, canonical_unit) -> (factor, offset)
_CONVERSIONS: dict[tuple[str, str], tuple[float, float]] = {
    ("bpm", "bpm"): (1.0, 0.0),
    ("ms", "ms"): (1.0, 0.0),
    ("s", "ms"): (1000.0, 0.0),
    ("count", "count"): (1.0, 0.0),
    ("min", "min"): (1.0, 0.0),
    ("h", "min"): (60.0, 0.0),
    ("s", "min"): (1.0 / 60.0, 0.0),
    ("pct", "pct"): (1.0, 0.0),
    ("mg/dL", "mg/dL"): (1.0, 0.0),
    ("mmol/L", "mg/dL"): (18.0182, 0.0),
    ("mmHg", "mmHg"): (1.0, 0.0),
    ("kg", "kg"): (1.0, 0.0),
    ("lb", "kg"): (0.45359237, 0.0),
    ("degC", "degC"): (1.0, 0.0),
    ("degF", "degC"): (5.0 / 9.0, -32.0 * 5.0 / 9.0),
    ("kcal", "kcal"): (1.0, 0.0),
    ("kJ", "kcal"): (1.0 / 4.184, 0.0),
}


def _canon_unit_name(unit: str) -> str:
    key = unit.strip()
    return _ALIASES.get(key) or _ALIASES.get(key.lower()) or key


def normalize(kind: MetricKind, value: float, unit: str) -> float:
    """Convert ``value`` (given in ``unit``) to ``kind``'s canonical unit.

    Raises :class:`UnitMismatchError` if there is no known conversion.
    """
    target = canonical_unit(kind)
    src = _canon_unit_name(unit)
    conv = _CONVERSIONS.get((src, target))
    if conv is None:
        raise UnitMismatchError(f"cannot convert {unit!r} to {target!r} for {kind.value}")
    factor, offset = conv
    return float(value) * factor + offset
