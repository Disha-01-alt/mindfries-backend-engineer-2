# ALIVE O.S. — architecture

A deliberately thin but realistically interconnected health-telemetry engine.
The two correctness invariants live at the center; every layer exists to serve
them and to make them testable without infrastructure.

## Layering

```
   api/        FastAPI edge: ingest a reading, read a score + lineage, aging, cohorts
     |
   worker/     processor: ingest -> recompute score -> evaluate alerts -> deliver
     |         scheduler: periodic sweeps on the injected clock
     v
   services/   ingest, scoring, alerting, dispatch, recommendations, coaching, cohorts
     |
   store/      sample_store, score_store, member_store, dispatch_log, outbox (in-memory)
     |
   core/       pure values + functions: sample, units, windows, dedup, score, aging, events
```

Each layer depends only downward. `core` is pure (no clock reads, no I/O); the
only wall-clock source in the whole engine is the injected `Clock`, read in the
worker and for processing-time stamps — never in scoring.

## The two invariants

### 1. As-of monotonicity (event time vs processing time)

Readings arrive out of order in **event time** — a band's 9:00 sample can reach
the engine after a phone's 9:05 sample, because the two sources sync on different
schedules. The invariant:

> A member's score always reflects the newest event-time reading observed for
> them; a late, older-event-time sample is folded into history but never
> regresses the score.

It is enforced in **one place** — `services/scoring.py`, which scores a member
*as of their maximum event time*, not as of whichever reading triggered the
recompute. Because the recompute runs over all the member's samples and
`core.score.compute` is a pure, order-independent function, a late reading is
incorporated into history without moving the watermark backwards.

The debug task plants a bug here (scoring as-of the just-processed reading) so a
late sample regresses the score; the fix restores the max-event-time watermark.

### 2. At-most-once dispatch (idempotency)

Delivery is at-least-once: the outbox is drained and dispatched, the worker can
retry, and a sweep can re-evaluate a score and re-emit the same alert. The
invariant:

> For each `(recipient, alert)` the engine delivers at most once.

The precondition is a **stable id born with the event**: `Alert.alert_id` is
derived from `(member, rule, window)` (`core/events.py`), identical across every
retry. The `DispatchLog` records delivered `(recipient, id)` pairs. The feature
task wires the dispatcher to consult it — deliver only if unseen, then record.

## Determinism

Everything that could make grading flake is a controlled input:

- **the clock is injected** (`ManualClock` in tests) — no sleeps, no wall-clock reads in logic;
- **stores are in-memory** — no database, no container;
- **scoring is pure and order-independent** — shuffle the samples, get the same score;
- **ids are content-derived** (`core/ids.stable_id`) — a re-sync produces the same id;
- **dedup is priority-based with total tie-breaks** — never arrival-order dependent.

## Domain model (grounding)

The data model follows **Open mHealth** (`DataPoint{header, body}`): a `Sample`
carries its measurement (metric, value, canonical unit) plus provenance (member,
device, source, event time, per-device sequence). Labs and check-ins are Samples
with a different `source`, so one pipeline serves all ingestion paths. Unit
normalization at the edge (`core/units.py`) mirrors Open mHealth's `unit_value`.
Window semantics (half-open tumbling, `core/windows.py`) and the event-time /
watermark model follow Flink/Kafka-Streams stream-processing concepts. The score
is a transparent rule engine (not an ML black box) so it is reproducible and
**traceable** — a lineage of per-metric contributions — which a health score a
coach acts on must be.

(References are architectural only; nothing here is copied. Permissive sources:
Open mHealth schemas, Apache-2.0; FHIR Observation, CC0; Flink/Kafka docs,
Apache-2.0. AGPL health-sync projects were deliberately avoided.)

## What's intentionally out of scope

In-memory only (no durable time-series store); single-process (no real
partitioned stream or cross-partition watermarks); in-process outbox (no real
broker); a transparent rule-based score (no ML model); no auth / PHI encryption.
Each of these is the subject of the **design task**, which takes the engine to
5M+ members while holding both invariants under concurrency and partial failure.
