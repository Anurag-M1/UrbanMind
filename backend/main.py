import asyncio
import logging
import os
from datetime import datetime
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from services.state_manager import state_manager
from services.mqtt_client import mqtt_client
from services import webster, simulator
from routers import video, signals, emergency, analytics, ws
from services.live_processor import live_processor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("urbanmind")

# Background tasks
_tasks: list[asyncio.Task] = []  # type: ignore


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown events."""
    logger.info("═══ UrbanMind API Starting ═══")
    start_time = datetime.utcnow()

    # 1. Connect Redis
    try:
        await state_manager.connect()
        logger.info("✓ Redis connected")
    except Exception as e:
        logger.error("✗ Redis connection failed: %s", e)

    # 1.25 Seed demo intersections on fresh deployments
    if settings.DEMO_MODE:
        try:
            intersections = await state_manager.get_all_intersections()
            if not intersections:
                from scripts_seed import seed_intersections

                await seed_intersections(state_manager)
                logger.info("✓ Demo intersections seeded")
            else:
                logger.info("✓ Demo intersections already present (%d)", len(intersections))
        except Exception as e:
            logger.error("✗ Demo intersection seeding failed: %s", e)

    # 1.5 Start Live Vision Processor
    try:
        await live_processor.start()
        logger.info("✓ Live Vision Processor started")
    except Exception as e:
        logger.error("✗ Live Vision Processor failed: %s", e)

    # 2. Connect MQTT
    try:
        mqtt_client.connect()
        logger.info("✓ MQTT connecting")
    except Exception as e:
        logger.warning("✗ MQTT connection failed (non-critical): %s", e)

    # 3. Set ws_broadcast on routers that need it
    video.set_ws_broadcast(ws.broadcast)
    emergency.set_ws_broadcast(ws.broadcast)

    # 4. Start WebSocket tick loop
    tick_task = asyncio.create_task(ws.tick_loop())
    _tasks.append(tick_task)
    logger.info("✓ WebSocket tick loop started")

    # 5. Start Webster optimization loop
    webster_task = asyncio.create_task(
        webster.optimization_loop(
            state_manager,
            mqtt_client,
            ws.broadcast,
            settings.WEBSTER_INTERVAL,
        )
    )
    _tasks.append(webster_task)
    logger.info("✓ Webster optimization loop started")

    # 6. Start traffic simulator (if DEMO_MODE)
    if settings.DEMO_MODE:
        sim_task = asyncio.create_task(
            simulator.simulation_loop(state_manager, ws.broadcast, interval=5)
        )
        _tasks.append(sim_task)
        logger.info("✓ Traffic simulator started (DEMO_MODE)")

    # Ensure uploads directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    logger.info("═══ UrbanMind API Ready ═══")

    yield

    # Shutdown
    logger.info("═══ UrbanMind API Shutting Down ═══")
    for task in _tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    # 0. Stop Live Vision Processor
    await live_processor.stop()

    mqtt_client.disconnect()
    await state_manager.disconnect()
    logger.info("═══ UrbanMind API Stopped ═══")


# Create FastAPI app
app = FastAPI(
    title="UrbanMind API",
    description="AI Traffic Flow Optimizer & Emergency Green Corridor",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for video uploads
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include routers
app.include_router(video.router)
app.include_router(signals.router)
app.include_router(emergency.router)
app.include_router(analytics.router)
app.include_router(ws.router)

_start_time = datetime.utcnow()


@app.get("/health")
async def health():
    """Health check endpoint."""
    redis_ok = await state_manager.is_connected()
    uptime = (datetime.utcnow() - _start_time).total_seconds()
    return {
        "status": "ok" if redis_ok else "degraded",
        "redis": "connected" if redis_ok else "disconnected",
        "mqtt": "connected" if mqtt_client.connected else "disconnected",
        "uptime_seconds": round(uptime, 1),
        "version": "1.0.0",
        "demo_mode": settings.DEMO_MODE,
    }


@app.get("/api/v1/demo/reset")
async def demo_reset():
    """Reset all state for a fresh demo."""
    await state_manager.reset_all()

    # Re-seed intersections
    from scripts_seed import seed_intersections
    await seed_intersections(state_manager)

    await ws.broadcast({"type": "demo_reset", "timestamp": datetime.utcnow().isoformat()})

    return {"reset": True, "message": "Demo state reset successfully"}
