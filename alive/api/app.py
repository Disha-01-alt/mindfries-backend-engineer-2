"""The FastAPI application factory.

Maps the engine's error taxonomy to HTTP: every ``AliveError`` carries a
``status`` and a stable ``code``, so a bad unit is a 400 with ``unit_mismatch``,
an unenrolled member a 409 with ``not_enrolled``, and so on — the API never
leaks a stack trace for a domain error.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ..core.errors import AliveError
from .routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="ALIVE O.S.", version="1.0", description="Goqii health-telemetry risk-scoring engine")

    @app.exception_handler(AliveError)
    async def _domain_error(_: Request, exc: AliveError) -> JSONResponse:
        return JSONResponse(status_code=exc.status, content={"code": exc.code, "message": exc.message})

    app.include_router(router)
    return app


app = create_app()
