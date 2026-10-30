"""Services — orchestration over the stores. Still no I/O of their own; they
coordinate the pure core and the in-memory stores into use cases (ingest a
reading, recompute a score, derive and dispatch alerts)."""
