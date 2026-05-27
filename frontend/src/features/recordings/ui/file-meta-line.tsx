/** File metadata line (recording date, duration, size, topic count, message count). Shared by recording/files.
 *
 * Putting the recording date on the left keeps the visual flow consistent with the descending-by-date list ordering.
 * Items are grouped time-related (date → duration) and count-related (size → topics → msgs).
 */

import { formatDuration, formatRecordingDate, formatSize } from "@/lib/format";

export function FileMetaLine({
  size,
  topicCount,
  recordingStartNs,
  durationNs,
  messageCount,
}: {
  size: number;
  topicCount: number | null;
  recordingStartNs: number | null;
  durationNs?: number | null;
  messageCount?: number | null;
}) {
  return (
    <div className="flex items-center gap-2 text-xs text-muted-foreground">
      <span className="tabular-nums">{formatRecordingDate(recordingStartNs, durationNs)}</span>
      <span>·</span>
      <span className="tabular-nums">{durationNs == null ? "---" : formatDuration(durationNs / 1_000_000_000)}</span>
      <span>·</span>
      <span className="tabular-nums">{formatSize(size)}</span>
      <span>·</span>
      <span className="tabular-nums">{topicCount ?? "---"} topics</span>
      <span>·</span>
      <span className="tabular-nums">{messageCount == null ? "---" : messageCount.toLocaleString()} msgs</span>
    </div>
  );
}
