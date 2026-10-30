"""In-memory stores — the only mutable state in the engine.

Append-only where the domain is append-only (samples are facts; you never edit a
reading that happened), latest-wins where the domain is a current view (a
member's score). No database, no network: deterministic by construction, and a
real persistence layer is the design task's subject.
"""
