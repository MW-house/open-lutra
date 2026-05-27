/** Custom hook for the Timeline API.
 *
 * Uses orval-generated getTimeline / getTimelineMessages, and waits for
 * background generation to finish with the same polling pattern as quality analysis.
 */

import { useGetTimeline, useGetTimelineMessages } from "@/api/generated/analysis/analysis";
import type { MessagesDetailResponse, TimelineResponse } from "@/api/generated/schemas";
import { useQualityTimelineStore } from "./store";

export function useTimeline(folderPath: string | null) {
  return useGetTimeline<TimelineResponse>(
    { path: folderPath ?? "" },
    {
      query: {
        enabled: !!folderPath,
        select: (resp) => resp.data as TimelineResponse,
        refetchInterval: (query) => {
          const status = (query.state.data?.data as TimelineResponse | undefined)?.status;
          return status === "analyzing" ? 2000 : false;
        },
      },
    },
  );
}

/** Calculation constants for the rug plot query range.
 *
 * - PREFETCH_BUFFER_SEC: fetch this many extra seconds before/after viewRange to prefetch
 * - SNAP_GRID_SEC: snap the query range to this grid to increase cache hits
 *
 * Effect: even when viewRange slides continuously during playback, the query key
 * does not change until a snap boundary is crossed, so no refetch is triggered
 * (→ real-time display). Refetch happens only about once every SNAP_GRID_SEC seconds.
 */
const PREFETCH_BUFFER_SEC = 15;
const SNAP_GRID_SEC = 10;

/** Aligns viewRange to the snap grid and returns a fetch range including the prefetch buffer. */
function snapFetchRange(fromSec: number, toSec: number): { from: number; to: number } {
  const rawFrom = Math.max(0, fromSec - PREFETCH_BUFFER_SEC);
  const rawTo = toSec + PREFETCH_BUFFER_SEC;
  const from = Math.max(0, Math.floor(rawFrom / SNAP_GRID_SEC) * SNAP_GRID_SEC);
  const to = Math.ceil(rawTo / SNAP_GRID_SEC) * SNAP_GRID_SEC;
  return { from, to };
}

/** For the rug plot: fetches message details within the given range.
 *
 * The actual fetch range adds a PREFETCH_BUFFER_SEC buffer around viewRange and
 * snaps to the SNAP_GRID_SEC grid. This way, even when viewRange slides continuously
 * during playback, no refetch happens until a snap boundary is crossed, and the
 * TanStack Query cache keeps the real-time display smooth.
 *
 * The display side (RugPlot) filters by the actual viewRange, so the buffer is
 * never visible. The caller also checks `MIN_VISIBLE_DURATION` (= rug plot's
 * display threshold < 10s) before passing it to enabled. Requests are suppressed
 * during dragging.
 */
export function useTimelineMessages(folderPath: string | null, topic: string | null, fromSec: number, toSec: number) {
  const isDragging = useQualityTimelineStore((s) => s.isDragging);
  const visibleSpan = toSec - fromSec;
  const enabled = !!folderPath && !!topic && visibleSpan > 0 && visibleSpan < 10 && !isDragging;
  const fetchRange = snapFetchRange(fromSec, toSec);
  return useGetTimelineMessages<MessagesDetailResponse>(
    { path: folderPath ?? "", topic: topic ?? "", from_sec: fetchRange.from, to_sec: fetchRange.to },
    {
      query: {
        enabled,
        // Keep staleTime long so we get cache hits within the same snap bucket during playback
        staleTime: 5 * 60_000,
        select: (resp) => resp.data as MessagesDetailResponse,
      },
    },
  );
}
