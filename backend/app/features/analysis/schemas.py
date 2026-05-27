"""Quality analysis and timeline API schemas.

Domain models (such as QualityReport) live in models.py.
"""

from pydantic import BaseModel, Field

from app.features.analysis.models import QualityReport

# ---------------------------------------------------------------------------
# Quality analysis
# ---------------------------------------------------------------------------


class QualityResponse(BaseModel):
    """Response body for GET /api/analysis/quality."""

    status: str = Field(..., pattern=r"^(ready|analyzing|not_found|error)$")
    report: QualityReport | None
    error: str | None


# ---------------------------------------------------------------------------
# Timeline
# ---------------------------------------------------------------------------


class TimelineBin(BaseModel):
    """A single timeline bin."""

    t: float = Field(..., description="Bin start time (seconds since recording start)")
    count: int = Field(..., description="Actual number of messages in the bin")
    expected: float = Field(..., description="Expected number of messages in the bin (float)")
    has_gap: bool = Field(..., description="Whether this bin contains a major loss (3+ frames)")
    has_minor_loss: bool = Field(..., description="Whether this bin contains a minor loss (1-2 frames)")


class TimelineGap(BaseModel):
    """Loss event on the timeline (IQR statistics based)."""

    start_sec: float
    end_sec: float
    duration_sec: float
    lost_count: int = Field(..., description="Estimated number of lost messages")
    severity: str = Field(..., description="minor (1-2 frames) / major (3+ frames)")


class TimelineTopic(BaseModel):
    """Per-topic timeline data."""

    name: str
    msg_type: str
    expected_hz: float
    bins: list[TimelineBin]
    gaps: list[TimelineGap]


class TimelineData(BaseModel):
    """Overall timeline data."""

    duration_sec: float
    bin_width_sec: float
    recording_start_ns: int = Field(
        ...,
        description="Recording start time (ns, header.stamp based). Origin for the rug plot's relative time display. 0 means legacy cache.",
    )
    log_time_offset_ns: int = Field(
        ...,
        description=(
            "Difference between log_time and header.stamp (ns). Adding this to "
            "recording_start_ns produces the filter range used against the MCAP "
            "log_time chunk index. Needed to correctly scan time ranges when the "
            "robot clock is not NTP-synced and drifts significantly."
        ),
    )
    topics: list[TimelineTopic]


class TimelineResponse(BaseModel):
    """Response body for GET /api/analysis/timeline."""

    status: str = Field(..., pattern=r"^(ready|analyzing|not_found|error)$")
    data: TimelineData | None = None
    error: str | None = None


class MessageDetailItem(BaseModel):
    """Per-message info used by the rug plot."""

    index: int
    timestamp_sec: float
    size_bytes: int


class MessagesDetailResponse(BaseModel):
    """Response body for GET /api/analysis/timeline/messages."""

    topic: str
    expected_hz: float
    messages: list[MessageDetailItem]
