"""Constants and helpers for MP4 / telemetry.json generation.

The actual generation lifecycle is managed by `JobQueue` in `app/features/jobs/`.
This module only exposes settings and helpers shared by `convert_mcap()` and
`JobQueue`.
"""

from pathlib import Path

# Fixed FPS (shared across previews)
VIDEO_FPS = 30


def list_videos(directory: Path) -> list[str]:
    """Return the list of MP4 file names in the recording directory."""
    return sorted(f.name for f in directory.glob("*.mp4"))
