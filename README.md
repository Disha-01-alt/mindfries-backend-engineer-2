# ALIVE O.S. — Goqii health-telemetry risk-scoring engine

A working, in-memory model of Goqii's **ALIVE O.S.**: it ingests continuous
biometric and activity telemetry from wearables, lab results and daily check-ins,
computes transparent, auditable **risk scores** and **aging assessments**, and
dispatches **recommendations** (to members) and **alerts** (to coaches).

This is an assessment codebase: candidates debug, extend, and design it. It is
deterministic and infra-free by design — no database, no broker, no network, an
injected clock — so behaviour is reproducible and tests never flake.

## Run it

The **core engine is pure stdlib** — the whole suite runs with just Python, no
dependencies, which is how the assessment is graded:

```bash
python3 -m unittest discover -s tests -t .
```

The HTTP API uses **FastAPI** (a real framework, so you navigate real code). It
needs its dependencies and is optional for the task — run it yourself to poke at
the engine:

```bash
pip install -r requirements.txt
uvicorn alive.api.app:app --port 8000
# GET  /members/m_risk/score     (seeded demo population: m_fit, m_drift, m_risk)
# GET  /members/m_fit/aging
# POST /ingest                   {member_id, device_id, metric, event_time, value, unit, seq, source}
# POST /cohorts/summary          {member_ids: [...]}
```

(The workspace doesn't auto-start the API — the grader runs the stdlib tests, so
nothing needs installing to work the task.)

## The two invariants this engine turns on

1. **As-of monotonicity.** A member's score always reflects their newest
   *event-time* reading; a late, older-event-time sample (a watch's 9:00 reading
   arriving after the phone's 9:05) is folded into history but **never regresses**
   the score to stale data.
2. **At-most-once dispatch.** Delivery is at-least-once (the worker retries, a
   sweep re-emits), so the *effect* is made at-most-once per `(recipient, alert)`
   via a stable, born-with-the-event id.

Both have the assessment signature: the happy path (ordered input, single fire)
passes; concurrency / out-of-order / retry is where a naive implementation breaks.

## Layout

```
alive/
  core/        pure, deterministic, I/O-free
    clock, ids, errors, metrics, units, sample, windows, dedup, score, aging, events
  store/       in-memory state
    sample_store (append-only, monotonic seq), score_store, member_store,
    dispatch_log (at-most-once), outbox
  services/    orchestration
    ingest, scoring (as-of invariant), alerting, dispatch (at-most-once),
    recommendations, coaching, cohorts
  worker/      runs on the injected clock
    processor (ingest->score->alert->dispatch), scheduler (sweeps)
  api/         FastAPI edge (schemas, routes, app)
  engine.py    composition root
  seed.py      deterministic demo population
tests/         stdlib unittest
_tasks/        debug / feature / design assessment tasks
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for the design in depth.

## Tasks

- **debug-score-regression** — a late sample regresses a member's score; restore
  as-of monotonicity (the bug lives in the scoring service's watermark choice).
- **feature-idempotent-dispatch** — make alert delivery at-most-once per recipient.
- **design-alive-platform** — take the engine to 5M+ members while keeping both
  invariants (discussion task).
