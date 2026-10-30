"""ALIVE O.S. — Goqii's health-telemetry risk-scoring engine (assessment build).

Ingests continuous biometric and activity telemetry from wearables, lab
results and daily check-ins; computes transparent, auditable risk scores and
aging assessments; and dispatches recommendations and coach alerts.

Architecture (see ARCHITECTURE.md):

    api        FastAPI edge: ingest samples, read scores + lineage, list alerts
    worker     drains pending samples on an injected clock, advances the
               watermark, triggers scoring and dispatch
    services   ingest / scoring / alerting / recommendations / coaching / cohorts
    store      in-memory: append-only samples, latest-score, dispatch dedup log
    core       pure, deterministic, I/O-free: Sample, units, windows, score

The engine is deterministic by construction — the only clock is injected, the
stores are in-memory, and scoring is a pure function of the observed events —
so the same events, in any arrival order, always yield the same score.
"""

__all__ = ["engine"]
