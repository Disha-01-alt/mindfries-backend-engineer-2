"""The pure core: deterministic, I/O-free domain logic.

Nothing in this package reads the wall clock, touches the network, or mutates
global state. Time arrives as an explicit `event_time` on a Sample or an
`as_of` argument; everything is a value or a pure function over values. That is
what makes the engine reproducible and the tests deterministic.
"""
