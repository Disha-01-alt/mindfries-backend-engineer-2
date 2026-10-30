"""The HTTP edge — a FastAPI app over the engine.

This is the only layer that depends on a third-party framework. The core engine
is pure stdlib, so the logic (and every assessment task) is tested without
FastAPI installed; these modules are imported only when the API actually runs.
"""
