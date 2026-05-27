"""Quality analysis and timeline API endpoints."""

import asyncio
import logging
from pathlib import Path

from fastapi import APIRouter, Depends

from app.dependencies import require_dir
from app.features.analysis.quality_analyzer import get_quality_analyzer
from app.features.analysis.schemas import (
    MessagesDetailResponse,
    QualityResponse,
    TimelineResponse,
)
from app.features.analysis.timeline_analyzer import TimelineAnalyzer, read_messages_in_range

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


# ---------------------------------------------------------------------------
# Quality analysis
# ---------------------------------------------------------------------------


@router.get("/quality", response_model=QualityResponse, operation_id="getQuality")
async def get_quality(  # pragma: no cover
    target: Path = Depends(require_dir),
) -> QualityResponse:
    """Get the MCAP file quality report (no side effects).

    Returns the cached report if available, otherwise returns only the
    current status. To kick off analysis, use POST /api/analysis/quality/analyze.
    """
    return await get_quality_analyzer().get(target)


@router.post("/quality/analyze", response_model=QualityResponse, operation_id="startQualityAnalysis")
async def start_quality_analysis(  # pragma: no cover
    target: Path = Depends(require_dir),
) -> QualityResponse:
    """Start quality analysis (idempotent: returns the existing job status if already running)."""
    return await get_quality_analyzer().start(target)


# ---------------------------------------------------------------------------
# Timeline
# ---------------------------------------------------------------------------


_timeline_analyzer = TimelineAnalyzer()


@router.get("/timeline", response_model=TimelineResponse, operation_id="getTimeline")
async def get_timeline(target: Path = Depends(require_dir)) -> TimelineResponse:  # pragma: no cover
    """Get the timeline data (no side effects).

    Returns cached data if available, otherwise returns only the current
    status. To kick off analysis, use POST /api/analysis/timeline/analyze.
    """
    result = await _timeline_analyzer.get(target)
    return TimelineResponse(**result)


@router.post("/timeline/analyze", response_model=TimelineResponse, operation_id="startTimelineAnalysis")
async def start_timeline_analysis(  # pragma: no cover
    target: Path = Depends(require_dir),
) -> TimelineResponse:
    """Start timeline analysis (idempotent: returns the existing job status if already running)."""
    result = await _timeline_analyzer.start(target)
    return TimelineResponse(**result)


@router.get("/timeline/messages", response_model=MessagesDetailResponse, operation_id="getTimelineMessages")
async def get_timeline_messages(  # pragma: no cover
    topic: str,
    from_sec: float,
    to_sec: float,
    target: Path = Depends(require_dir),
) -> MessagesDetailResponse:
    """Get message details for the specified time range (used for rug plots).

    Read from MCAP each time without caching. Use this for narrow time ranges.
    """
    return await asyncio.to_thread(read_messages_in_range, target, topic, from_sec, to_sec)
