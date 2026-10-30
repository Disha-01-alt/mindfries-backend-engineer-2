"""The worker — the thing that runs on the injected clock.

It drives the pipeline (ingest -> rescore -> alert -> dispatch) and, on a
schedule, sweeps members to recompute and re-evaluate. It is where delivery is
at-least-once: the outbox is drained and dispatched, and a sweep can re-emit an
alert the engine already produced.
"""
