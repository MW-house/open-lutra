/** Timeline horizontal-bar heatmap: shows per-topic message density with color shading.
 *
 * Density is computed from each bin's count/expected, and rendered as a gradient
 * from green (healthy) to red (missing). Gap regions are highlighted with a
 * semi-transparent red overlay.
 *
 * The display range is **always the entire recording** (start to end) and does not
 * follow the minimap's viewRange (= it works as a full-overview map). The current
 * viewRange is shown as a semi-transparent band overlay so users can see which
 * region is zoomed in.
 */

import { Activity } from "lucide-react";
import { useCallback, useMemo } from "react";
import type { TimelineData, TimelineTopic } from "@/api/generated/schemas";
import { sortTopicsByCategory } from "@/lib/topic-sort";
import { useQualityTimelineStore } from "../store";

/** Returns the background color for a bin. Decision is based on has_gap; count=0 is also considered.
 * Green = OK, red = gap. Regions without data are gray.
 */
function binColor(count: number, hasGap: boolean, hasMinorLoss: boolean, hasData: boolean): string {
  if (!hasData) return "bg-muted/10";
  if (hasGap) return "bg-red-400/50";
  if (hasMinorLoss) return "bg-amber-400/50";
  if (count === 0) return "bg-muted/20";
  return "bg-emerald-400/40";
}

/** Shortens a topic name for display. */
function shortName(name: string): string {
  const parts = name.split("/").filter(Boolean);
  return parts.length <= 2 ? parts.join("/") : parts.slice(0, 2).join("/");
}

/** Checks whether a gap matches the currently hovered loss event, with floating-point tolerance.
 *
 * loss_event comes from quality_analyzer and TimelineGap comes from timeline_analyzer; they
 * go through different aggregation code, so rounding errors can occasionally produce slightly
 * different values. A 10ms tolerance — well below frame time — is used for matching.
 */
function isHoveredGap(
  gapStartSec: number,
  topicName: string,
  hoveredLoss: { topicName: string; timestampSec: number } | null,
): boolean {
  if (!hoveredLoss) return false;
  if (hoveredLoss.topicName !== topicName) return false;
  return Math.abs(gapStartSec - hoveredLoss.timestampSec) < 0.01;
}

function TopicRow({
  topic,
  totalDuration,
  binWidth,
  viewRangeBand,
  hoveredLoss,
}: {
  topic: TimelineTopic;
  /** Total recording length (seconds). The display range is fixed to this. */
  totalDuration: number;
  binWidth: number;
  /** Percentages for overlaying the current minimap range as a semi-transparent band (null to hide). */
  viewRangeBand: { leftPct: number; widthPct: number } | null;
  /** Loss event hovered in the quality detail panel. The matching gap is highlighted. */
  hoveredLoss: { topicName: string; timestampSec: number } | null;
}) {
  // Compute bin positions relative to the whole recording (independent of viewRange)
  const safeDuration = totalDuration > 0 ? totalDuration : topic.bins.length * binWidth || 1;

  return (
    <div className="flex items-center gap-2 py-1">
      {/* Topic name */}
      <div className="w-28 shrink-0 truncate text-[11px] text-muted-foreground" title={topic.name}>
        {shortName(topic.name)}
      </div>

      {/* Heatmap bar (always shows the whole recording).
       * overflow-hidden is intentionally removed so the highlight glow / -inset-1 can extend outside. */}
      <div className="relative flex-1 flex h-4 rounded-sm bg-muted/20">
        {topic.bins.map((bin) => {
          const left = (bin.t / safeDuration) * 100;
          const width = (binWidth / safeDuration) * 100;
          return (
            <div
              key={bin.t}
              className={`absolute top-0 h-full ${binColor(bin.count, bin.has_gap, bin.has_minor_loss, bin.count > 0 || bin.expected > 0)}`}
              style={{ left: `${left}%`, width: `${Math.max(width, 0.2)}%` }}
            />
          );
        })}

        {/* Gap overlays. Gaps matching the hovered loss event are highlighted in cyan.
         * Color scheme matches the bin shading: amber for minor (1-2 frames), red for major (3+ frames). */}
        {topic.gaps.map((gap) => {
          const left = (gap.start_sec / safeDuration) * 100;
          const width = (gap.duration_sec / safeDuration) * 100;
          const highlighted = isHoveredGap(gap.start_sec, topic.name, hoveredLoss);
          const severityClass =
            gap.severity === "minor"
              ? "border-x border-amber-500/50 bg-amber-400/20"
              : "border-x border-red-500/50 bg-red-500/20";
          const baseClass = highlighted
            ? "border-x border-cyan-300 bg-cyan-300/40 shadow-[0_0_8px_2px_rgba(103,232,249,0.7)] -inset-y-1 z-10"
            : severityClass;
          return (
            <div
              key={gap.start_sec}
              className={`absolute top-0 h-full ${baseClass}`}
              style={{ left: `${left}%`, width: `${Math.max(width, 0.3)}%` }}
              title={`gap ${gap.duration_sec.toFixed(2)}s / ~${gap.lost_count} msgs`}
            />
          );
        })}

        {/* viewRange band: overlays the range currently filtered in the minimap, semi-transparent. */}
        {viewRangeBand && (
          <div
            className="pointer-events-none absolute top-0 h-full border-x border-cyan-400/70 bg-cyan-400/10"
            style={{ left: `${viewRangeBand.leftPct}%`, width: `${Math.max(viewRangeBand.widthPct, 0.5)}%` }}
          />
        )}
      </div>

      {/* Frequency */}
      <span className="w-14 shrink-0 text-right text-[10px] tabular-nums text-muted-foreground">
        {topic.expected_hz > 0 ? `${topic.expected_hz}Hz` : "-"}
      </span>
    </div>
  );
}

export function TimelineHeatmap({ data }: { data: TimelineData }) {
  const viewRange = useQualityTimelineStore((s) => s.viewRange);
  const selectedTopic = useQualityTimelineStore((s) => s.selectedTopic);
  const setSelectedTopic = useQualityTimelineStore((s) => s.setSelectedTopic);
  const hoveredLoss = useQualityTimelineStore((s) => s.hoveredLossEvent);

  const handleTopicClick = useCallback(
    (name: string) => {
      setSelectedTopic(selectedTopic === name ? null : name);
    },
    [selectedTopic, setSelectedTopic],
  );

  // Unified ordering (images on top, joints on the bottom, alphabetical within each category)
  const sortedTopics = useMemo(
    () =>
      sortTopicsByCategory(
        data.topics,
        (t) => t.name,
        (t) => t.msg_type,
      ),
    [data.topics],
  );

  // viewRange band (overlays the current display range with semi-transparency).
  // The heatmap itself always shows the whole recording, so we only convert the band position to %.
  const totalDuration = data.duration_sec > 0 ? data.duration_sec : 1;
  const isPartial = viewRange.to - viewRange.from > 0 && viewRange.to - viewRange.from < totalDuration;
  const viewRangeBand = isPartial
    ? {
        leftPct: (viewRange.from / totalDuration) * 100,
        widthPct: ((viewRange.to - viewRange.from) / totalDuration) * 100,
      }
    : null;

  if (!sortedTopics.length) {
    return <p className="text-xs text-muted-foreground">No topic data available</p>;
  }

  return (
    <div>
      <div className="flex items-center gap-2 mb-2">
        <Activity size={14} className="text-muted-foreground" />
        <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Timeline</span>
      </div>

      <div className="rounded-md border border-border p-2 space-y-0.5">
        {sortedTopics.map((topic) => (
          <div
            key={topic.name}
            className={`rounded px-1 transition-colors cursor-pointer ${
              selectedTopic === topic.name
                ? "bg-cyan-500/15 shadow-[inset_3px_0_0_0_rgb(34,211,238)]"
                : "hover:bg-muted/20"
            }`}
            onClick={() => handleTopicClick(topic.name)}
          >
            <TopicRow
              topic={topic}
              totalDuration={data.duration_sec}
              binWidth={data.bin_width_sec}
              viewRangeBand={viewRangeBand}
              hoveredLoss={hoveredLoss}
            />
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="mt-1.5 flex gap-3 text-[10px] text-muted-foreground">
        <span className="flex items-center gap-1">
          <span className="inline-block h-2 w-3 rounded-sm bg-emerald-400/40" /> OK
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-2 w-3 rounded-sm bg-amber-400/50" /> 1-2 frame loss
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-2 w-3 rounded-sm bg-red-400/50" /> 3+ frame loss
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-2 w-3 rounded-sm border-x border-cyan-400/60 bg-cyan-400/10" />
          Viewing
        </span>
      </div>
    </div>
  );
}
