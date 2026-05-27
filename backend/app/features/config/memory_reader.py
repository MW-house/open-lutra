"""Module for retrieving container memory usage.

Falls back through cgroup v2 -> v1 -> /proc to read memory information.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def read_usage_bytes() -> int:
    """Get the container memory usage in bytes.

    Falls back through cgroup v2 memory.current -> /proc/self/status VmRSS.
    memory.current returns the entire container's usage (including cache).
    """
    # cgroup v2 (entire container usage)
    cg2 = Path("/sys/fs/cgroup/memory.current")
    if cg2.exists():
        try:
            return int(cg2.read_text().strip())
        except (OSError, ValueError) as e:
            logger.debug("Failed to read cgroup v2 memory.current: %s", e)

    # Fallback: per-process RSS
    try:
        for line in Path("/proc/self/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) * 1024  # kB -> bytes
    except (OSError, ValueError) as e:
        logger.debug("Failed to read /proc/self/status: %s", e)
    return 0


def read_limit_bytes() -> int | None:
    """Get the container memory limit in bytes.

    Falls back through cgroup v2 -> v1.
    Returns MemTotal from /proc/meminfo when the container has no limit.
    """
    # cgroup v2
    cg2 = Path("/sys/fs/cgroup/memory.max")
    if cg2.exists():
        val = cg2.read_text().strip()
        if val != "max":
            return int(val)
        return _read_memtotal()

    # cgroup v1
    cg1 = Path("/sys/fs/cgroup/memory/memory.limit_in_bytes")
    if cg1.exists():
        try:
            val_int = int(cg1.read_text().strip())
            if val_int < 2**62:
                return val_int
        except (OSError, ValueError) as e:
            logger.debug("Failed to read cgroup v1 memory.limit_in_bytes: %s", e)
        return _read_memtotal()

    return _read_memtotal()


def _read_memtotal() -> int | None:
    """Get total memory from /proc/meminfo."""
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal:"):
                return int(line.split()[1]) * 1024  # kB -> bytes
    except (OSError, ValueError) as e:
        logger.debug("Failed to read /proc/meminfo: %s", e)
    return None
