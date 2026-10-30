# Make alert dispatch at-most-once

## Background

As part of the server-side logic powering our web and mobile apps, our backend engine emits an **alert** (to a coach) or a **recommendation** (to a member) when a score crosses a threshold. Events are enqueued to an outbox and processed by a worker. Delivery is currently **at-least-once**: worker retries or scheduled sweeps can reprocess the outbox and re-emit duplicate events to client applications.

Duplicate notifications degrade user trust across web and mobile clients.

## What to build

Update the dispatch service logic to guarantee **at-most-once per recipient, per alert**. Any duplicate alert handed to the dispatcher must only be delivered the first time.

The backend infrastructure is already in place:

- Every alert and recommendation carries a **stable id** generated from the underlying event — `Alert.alert_id` / `Recommendation.rec_id` are derived from `(member, rule/kind, window)`, ensuring identical rule evaluations share the same id across retries (see `alive/core/events.py`).
- The database store `DispatchLog` (`alive/store/dispatch_log.py`) tracks which `(recipient, id)` pairs have already gone out.
- `alive/services/dispatch.py` provides a `_dedup_key(item)` helper returning the `(recipient, id)` for an alert or recommendation.

Wire this server-side logic together in `Dispatcher.dispatch`:

- deliver only if this recipient hasn't already received this id,
- record it after delivering,
- return `True` if it went out, `False` if it was suppressed as a duplicate.

## Notes

- At-most-once is keyed on the **stable id**, not an arrival counter — ensuring deduplication survives queue retries and worker re-enqueues.
- "At most once" is *per `(recipient, id)`*, not "once ever": a genuinely new alert (such as a different window) must still be delivered. Don't suppress across windows.
- Don't change the tests that ship with the product; they must keep passing.