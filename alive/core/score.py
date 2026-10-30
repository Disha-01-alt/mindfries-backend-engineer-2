"""The scoring core — a pure, deterministic, auditable risk model.

``compute`` turns a member's samples into a :class:`RiskScore`: an overall
0–100 risk (higher is worse), a band, and a **lineage** of per-metric
contributions (what each metric aggregated to, how much risk it carried, and
why). The lineage is the point — a health score a coach acts on must be
*traceable to the source values and the formula* (**B5**), not a black box.

Two properties this module guarantees, both tested:

  * **Determinism / order-independence** — ``compute`` depends only on the set
    of samples and the ``as_of`` watermark, never on their arrival order, the
    wall clock, or dict iteration order. Shuffle the input and the score is
    byte-for-byte identical.
  * **As-of honesty** — the returned score carries the ``as_of`` it was computed
    for. It is the *scoring service* (not this function) that decides the
    watermark; this function faithfully scores "as of" whatever it's told, which
    is what lets the service enforce that a score never regresses (B1).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable

from .dedup import dedupe
from .metrics import Aggregation, Direction, MetricKind, spec_for
from .sample import Sample
from .windows import DAY, window_start

SCORING_HORIZON = 7 * DAY  # a score reflects the last week of readings


class RiskBand(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


def band_for(overall: float) -> RiskBand:
    if overall < 25:
        return RiskBand.LOW
    if overall < 50:
        return RiskBand.MODERATE
    if overall < 75:
        return RiskBand.HIGH
    return RiskBand.CRITICAL


@dataclass(frozen=True)
class Contribution:
    metric: MetricKind
    aggregate: float      # the aggregated value, in canonical units
    sample_count: int     # how many samples fed the aggregate
    risk: float           # 0..100 risk this metric carried
    weight: float
    note: str


@dataclass(frozen=True)
class RiskScore:
    member_id: str
    as_of: float                      # the event-time watermark this score is "as of"
    overall: float                    # 0..100, higher = worse
    band: RiskBand
    sample_count: int
    contributions: tuple[Contribution, ...] = field(default_factory=tuple)

    @property
    def has_data(self) -> bool:
        return self.sample_count > 0


def _daily_sum_mean(samples: list[Sample]) -> float:
    """Mean of per-day totals — a 'typical day' for a cumulative metric."""
    by_day: dict[float, float] = {}
    for s in samples:
        d = window_start(s.event_time, DAY)
        by_day[d] = by_day.get(d, 0.0) + s.value
    return sum(by_day.values()) / len(by_day) if by_day else 0.0


def _aggregate(samples: list[Sample], agg: Aggregation) -> float:
    if agg is Aggregation.SUM:
        return _daily_sum_mean(samples)
    if agg is Aggregation.MEAN:
        return sum(s.value for s in samples) / len(samples)
    if agg is Aggregation.MIN:
        return min(s.value for s in samples)
    if agg is Aggregation.MAX:
        return max(s.value for s in samples)
    if agg is Aggregation.LATEST:
        return max(samples, key=lambda s: (s.event_time, s.seq)).value
    raise ValueError(f"unknown aggregation {agg!r}")


def _metric_risk(value: float, low: float, high: float, direction: Direction) -> float:
    """0 while the value is inside its healthy band, rising to 100 as it leaves.

    The slope is scaled by the half-width of the healthy band, so a metric with a
    wide healthy range tolerates more deviation before it reads as risk. The
    direction decides *which* boundary matters: for a "higher is better" metric
    (steps, HRV) only falling below ``low`` is risk — exceeding ``high`` never
    is; for "lower is better" (resting heart rate) only rising above ``high`` is.
    """
    span = max((high - low) / 2.0, 1e-9)

    if direction is Direction.HIGHER_BETTER:
        if value >= low:
            return 0.0
        return min(100.0, (low - value) / span * 50.0)

    if direction is Direction.LOWER_BETTER:
        if value <= high:
            return 0.0
        return min(100.0, (value - high) / span * 50.0)

    # IN_RANGE: risk grows with distance outside [low, high] in either direction.
    if low <= value <= high:
        return 0.0
    dist = (low - value) if value < low else (value - high)
    return min(100.0, dist / span * 50.0)


def compute(member_id: str, samples: Iterable[Sample], as_of: float, horizon: float = SCORING_HORIZON) -> RiskScore:
    """Score ``member_id`` as of the ``as_of`` watermark, over the trailing
    ``horizon``. Pure: identical output for any ordering of ``samples``."""
    window_lo = as_of - horizon
    # Dedupe defensively and keep only the trailing horizon up to the watermark.
    relevant = [s for s in dedupe(samples) if window_lo < s.event_time <= as_of]

    by_metric: dict[MetricKind, list[Sample]] = {}
    for s in relevant:
        by_metric.setdefault(s.metric, []).append(s)

    contributions: list[Contribution] = []
    weighted_sum = 0.0
    weight_total = 0.0
    # Iterate the registry in its fixed order, not dict insertion order, so the
    # lineage is deterministic regardless of which metric arrived first.
    for metric in MetricKind:
        ms = by_metric.get(metric)
        if not ms:
            continue
        spec = spec_for(metric)
        agg = _aggregate(ms, spec.aggregation)
        risk = _metric_risk(agg, spec.healthy_low, spec.healthy_high, spec.direction)
        note = _explain(metric, agg, risk, spec.healthy_low, spec.healthy_high)
        contributions.append(Contribution(metric, round(agg, 4), len(ms), round(risk, 2), spec.weight, note))
        weighted_sum += risk * spec.weight
        weight_total += spec.weight

    overall = round(weighted_sum / weight_total, 2) if weight_total else 0.0
    return RiskScore(
        member_id=member_id,
        as_of=as_of,
        overall=overall,
        band=band_for(overall),
        sample_count=len(relevant),
        contributions=tuple(contributions),
    )


def _explain(metric: MetricKind, agg: float, risk: float, low: float, high: float) -> str:
    where = "within range" if risk == 0 else ("below" if agg < low else "above") + " the healthy range"
    return f"{metric.value} averaged {round(agg, 2)} ({where} {low}–{high}); risk {round(risk, 1)}"
