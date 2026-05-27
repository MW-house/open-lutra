"""Job API endpoints (REST + SSE)."""

import asyncio
import logging
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.features.jobs.schemas import JobSchema, JobsResponse
from app.features.jobs.service import get_job_queue

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("", response_model=JobsResponse, operation_id="getJobs")
async def list_jobs() -> JobsResponse:
    """Get the current job list (active + history)."""
    queue = get_job_queue()
    return JobsResponse(jobs=[JobSchema.from_job(j) for j in queue.list_jobs()])


@router.get("/stream", operation_id="streamJobs")
async def stream_jobs(request: Request) -> StreamingResponse:  # pragma: no cover
    """Stream job status changes over SSE.

    Sends the current queue snapshot on connect, then streams status change events.
    """
    queue = get_job_queue()

    async def event_generator() -> AsyncGenerator[str, None]:
        async for event in queue.subscribe():
            if await request.is_disconnected():
                break
            data = event.data.model_dump_json()
            yield f"event: {event.event}\ndata: {data}\n\n"
            # Periodically yield so we can detect disconnects
            await asyncio.sleep(0)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
