import os
import uuid
import logging
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException

from services.video_processor import video_processor
from services.state_manager import state_manager
from config import settings

logger = logging.getLogger("urbanmind.router.video")
router = APIRouter(prefix="/api/v1/video", tags=["video"])

# Reference to ws_broadcast — set from main.py
ws_broadcast = None


def set_ws_broadcast(fn):  # type: ignore
    global ws_broadcast
    ws_broadcast = fn


@router.post("/upload")
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    intersection_id: str = Form("int_001"),
):
    """Upload a traffic video for YOLOv8 analysis."""
    # Validate file type
    allowed_exts = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
    ext = os.path.splitext(file.filename or "video.mp4")[1].lower()
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_exts)}",
        )

    # Generate video ID and save file
    video_id = uuid.uuid4().hex[:12]
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, f"{video_id}{ext}")

    # Check file size
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.MAX_VIDEO_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.1f}MB). Max: {settings.MAX_VIDEO_SIZE_MB}MB",
        )

    with open(file_path, "wb") as f:
        f.write(content)

    logger.info("Video uploaded: %s (%.1f MB)", file_path, size_mb)

    # Launch background analysis
    background_tasks.add_task(
        video_processor.analyze_video,
        file_path,
        video_id,
        intersection_id,
        ws_broadcast,
    )

    return {
        "video_id": video_id,
        "filename": file.filename,
        "size_mb": round(size_mb, 2),
        "status": "processing",
        "message": f"Analysis started. Poll /api/v1/video/{video_id}/status",
    }


@router.get("/{video_id}/status")
async def get_video_status(video_id: str):
    """Get current analysis status for a video."""
    result = video_processor.get_job_status(video_id)
    if not result:
        raise HTTPException(status_code=404, detail="Video analysis not found")

    progress_pct = 0.0
    if result.total_frames > 0 and result.status == "processing":
        progress_pct = min(99.0, (result.frames_processed / result.total_frames) * 100)
    elif result.status == "complete":
        progress_pct = 100.0

    data = result.model_dump(mode="json")
    data["progress_pct"] = round(progress_pct, 1)
    # Remove heavy fields from status poll to reduce bandwidth
    if result.status == "processing":
        data.pop("detection_frames", None)
    return data


@router.get("/{video_id}/frames")
async def get_video_frames(video_id: str, limit: int = 10):
    """Get annotated detection frames for a video."""
    result = video_processor.get_job_status(video_id)
    if not result:
        raise HTTPException(status_code=404, detail="Video analysis not found")
    frames = result.detection_frames[:limit]
    return {"video_id": video_id, "frames": [f.model_dump(mode="json") for f in frames]}


@router.post("/{video_id}/apply")
async def apply_video_timings(video_id: str):
    """Apply recommended signal timings from video analysis to the intersection."""
    result = video_processor.get_job_status(video_id)
    if not result:
        raise HTTPException(status_code=404, detail="Video analysis not found")
    if result.status != "complete":
        raise HTTPException(status_code=400, detail="Analysis not complete yet")

    timings = result.recommended_timings
    if not timings:
        raise HTTPException(status_code=400, detail="No recommended timings available")

    # Apply to all detected intersections
    for int_id in result.intersections_detected:
        intersection = await state_manager.get_intersection(int_id)
        if intersection:
            intersection.ew_green_duration = timings.get("ew_green", intersection.ew_green_duration)
            intersection.ns_green_duration = timings.get("ns_green", intersection.ns_green_duration)
            intersection.cycle_length = timings.get("cycle_length", intersection.cycle_length)
            await state_manager.set_intersection(intersection)

    if ws_broadcast:
        await ws_broadcast({
            "type": "timings_applied",
            "video_id": video_id,
            "timings": timings,
            "intersections": result.intersections_detected,
        })

    return {"applied": True, "timings": timings, "intersections": result.intersections_detected}


@router.get("/list")
async def list_videos():
    """List all analyzed videos."""
    videos = []
    for vid, result in video_processor.job_store.items():
        videos.append({
            "video_id": vid,
            "filename": result.filename,
            "status": result.status,
            "duration_seconds": result.duration_seconds,
            "vehicle_counts": result.vehicle_counts,
            "processing_time_seconds": result.processing_time_seconds,
        })
    return {"videos": videos}


@router.delete("/{video_id}")
async def delete_video(video_id: str):
    """Delete a video and its analysis."""
    result = video_processor.job_store.pop(video_id, None)
    if not result:
        raise HTTPException(status_code=404, detail="Video not found")

    # Try to delete file
    for ext in [".mp4", ".avi", ".mov", ".mkv", ".webm"]:
        path = os.path.join(settings.UPLOAD_DIR, f"{video_id}{ext}")
        if os.path.exists(path):
            os.remove(path)
            break

    return {"deleted": True, "video_id": video_id}
