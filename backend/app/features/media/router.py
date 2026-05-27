"""MP4 video and Joint API endpoints (for the preview panel on the recording detail page)."""

import asyncio
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from app.dependencies import require_dir
from app.features.jobs.models import JobStatus
from app.features.jobs.service import get_job_queue
from app.features.media.joint_reader import JointTopicsResponse, read_joint_data
from app.features.media.schemas import VideoResponse
from app.features.media.video_generator import list_videos

router = APIRouter(prefix="/api/media", tags=["media"])


# ---------------------------------------------------------------------------
# Video (MP4)
# ---------------------------------------------------------------------------


@router.get("/video", response_model=VideoResponse, operation_id="getVideoStatus")
async def get_video_status(target: Path = Depends(require_dir)) -> VideoResponse:  # pragma: no cover
    """Return the MP4 generation status (no side effects).

    If MP4 files already exist, returns the file list.
    Generation is triggered via POST /api/media/video/generate.
    """
    queue = get_job_queue()
    videos = list_videos(target)

    if videos:
        existing = queue.get_active_media_job(target)
        return VideoResponse(
            status="ready",
            videos=videos,
            progress=None,
            error=None,
            job_id=existing.job_id if existing else None,
        )

    active = queue.get_active_media_job(target)
    if active is not None:
        if active.status == JobStatus.FAILED:
            return VideoResponse(
                status="error",
                videos=[],
                progress=None,
                error=active.error or "Video generation failed",
                job_id=active.job_id,
            )
        if active.status in (JobStatus.QUEUED, JobStatus.RUNNING):
            return VideoResponse(
                status="generating",
                videos=[],
                progress={
                    "step": active.progress.step,
                    "step_label": active.progress.step_label,
                    "current": active.progress.current,
                    "total": active.progress.total,
                },
                error=None,
                job_id=active.job_id,
            )

    if not list(target.glob("*.mcap")):
        return VideoResponse(
            status="error",
            videos=[],
            progress=None,
            error="MCAP file not found",
            job_id=None,
        )

    return VideoResponse(
        status="not_generated",
        videos=[],
        progress=None,
        error=None,
        job_id=None,
    )


@router.post("/video/generate", response_model=VideoResponse, operation_id="startVideoGeneration")
async def start_video_generation(  # pragma: no cover
    target: Path = Depends(require_dir),
) -> VideoResponse:
    """Start MP4 generation (idempotent: returns the existing job status if already running)."""
    queue = get_job_queue()
    videos = list_videos(target)

    if videos:
        existing = queue.get_active_media_job(target)
        return VideoResponse(
            status="ready",
            videos=videos,
            progress=None,
            error=None,
            job_id=existing.job_id if existing else None,
        )

    if not list(target.glob("*.mcap")):
        return VideoResponse(
            status="error",
            videos=[],
            progress=None,
            error="MCAP file not found",
            job_id=None,
        )

    job = await queue.enqueue_generate_media(target)

    if job.status == JobStatus.FAILED:
        return VideoResponse(
            status="error",
            videos=[],
            progress=None,
            error=job.error or "Video generation failed",
            job_id=job.job_id,
        )

    return VideoResponse(
        status="generating",
        videos=list_videos(target),
        progress={
            "step": job.progress.step,
            "step_label": job.progress.step_label,
            "current": job.progress.current,
            "total": job.progress.total,
        },
        error=None,
        job_id=job.job_id,
    )


@router.get("/video/file", operation_id="getVideoFile")
async def get_video_file(name: str, target: Path = Depends(require_dir)) -> FileResponse:  # pragma: no cover
    """Stream a generated MP4 file."""
    if "/" in name or "\\" in name or ".." in name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file name")

    video_path = target / name
    if not video_path.is_file() or not video_path.suffix == ".mp4":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video file not found")

    return FileResponse(video_path, media_type="video/mp4")


# ---------------------------------------------------------------------------
# Joint time series (for preview graphs)
# ---------------------------------------------------------------------------


@router.get("/joints", response_model=JointTopicsResponse, operation_id="getJoints")
async def get_joints(  # pragma: no cover
    target: Path = Depends(require_dir),
    topic: str | None = None,
    decimation: int = 1,
) -> JointTopicsResponse:
    """Return JointState time-series data.

    Decodes JointState messages from MCAP and returns a position time series.
    Use decimation to down-sample (default: 1 = all data).
    """
    return await asyncio.to_thread(read_joint_data, target, topic, decimation)
