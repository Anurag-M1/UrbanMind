"""FastAPI entrypoint for the UrbanMind traffic orchestration backend."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from routers import analytics, emergency, intersections, signals, ws
from services import state_manager
from services.signal_controller import connect_mqtt, disconnect_mqtt, is_mqtt_connected, signal_adapter
from services.webster import webster_optimizer_loop

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger("urbanmind.api")

_background_tasks: list[asyncio.Task[None]] = []


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Connect infrastructure and launch background workers on startup."""

    await state_manager.connect_redis()
    await signal_adapter.connect()
    await connect_mqtt()

    _background_tasks.append(asyncio.create_task(webster_optimizer_loop()))
    _background_tasks.append(asyncio.create_task(ws.broadcast_loop()))

    try:
        yield
    finally:
        for task in _background_tasks:
            task.cancel()
        for task in _background_tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass
        _background_tasks.clear()
        await disconnect_mqtt()
        await state_manager.close_redis()


app = FastAPI(title="UrbanMind API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(signals.router, prefix=settings.API_PREFIX)
app.include_router(intersections.router, prefix=settings.API_PREFIX)
app.include_router(emergency.router, prefix=settings.API_PREFIX)
app.include_router(analytics.router, prefix=settings.API_PREFIX)
app.include_router(ws.router)


@app.get("/health")
async def health() -> dict[str, object]:
    """Return infrastructure health status for Docker and readiness checks."""

    return {
        "status": "ok",
        "redis": "connected" if await state_manager.ping_redis() else "disconnected",
        "mqtt": "connected" if is_mqtt_connected() else "disconnected",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Return a timestamped JSON error envelope for uncaught exceptions."""

    logger.error("Unhandled application error: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "timestamp": datetime.utcnow().isoformat()},
    )
