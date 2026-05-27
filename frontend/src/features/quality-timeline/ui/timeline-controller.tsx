/** Timeline Controller: a fixed controller for playback, seeking, and zoom.
 *
 * Always pinned to the bottom of the right panel. Composed of control buttons + a seek bar + a minimap.
 */

import { ChevronFirst, ChevronLast, ChevronLeft, ChevronRight, Pause, Play, ZoomIn, ZoomOut } from "lucide-react";
import { useCallback, useEffect, useRef } from "react";
import type { TimelineData } from "@/api/generated/schemas";
import { formatDuration } from "@/lib/format";
import { useQualityTimelineStore } from "../store";
import { Minimap } from "./minimap";

/** Frame step (seconds): based on 30fps */
const FRAME_STEP = 1 / 30;
/** Jump step (seconds) */
const JUMP_STEP = 5;
/** Zoom factor */
const ZOOM_FACTOR = 0.7;
/** Minimum view range (seconds) */
const MIN_VIEW_RANGE = 1;

function ControlButton({
  onClick,
  children,
  title,
}: {
  onClick: () => void;
  children: React.ReactNode;
  title: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex h-7 w-7 items-center justify-center rounded text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
      title={title}
    >
      {children}
    </button>
  );
}

/** Large circular play/pause button (echoing the record button's visual style). */
function PlayPauseButton({ isPlaying, onClick }: { isPlaying: boolean; onClick: () => void }) {
  const colorClass = isPlaying
    ? "bg-amber-500 hover:bg-amber-400 text-background"
    : "bg-emerald-500 hover:bg-emerald-400 text-background";
  return (
    <button
      type="button"
      onClick={onClick}
      title={isPlaying ? "Pause (Space)" : "Play (Space)"}
      className={`flex h-10 w-10 items-center justify-center rounded-full transition-all active:scale-95 shadow-md ${colorClass}`}
    >
      {isPlaying ? <Pause size={18} fill="currentColor" /> : <Play size={18} fill="currentColor" className="ml-0.5" />}
    </button>
  );
}

export function TimelineController({ data }: { data: TimelineData | null }) {
  const durationSec = useQualityTimelineStore((s) => s.durationSec);
  const playheadSec = useQualityTimelineStore((s) => s.playheadSec);
  const isPlaying = useQualityTimelineStore((s) => s.isPlaying);
  const viewRange = useQualityTimelineStore((s) => s.viewRange);
  const setPlayheadSec = useQualityTimelineStore((s) => s.setPlayheadSec);
  const setIsPlaying = useQualityTimelineStore((s) => s.setIsPlaying);
  const setViewRange = useQualityTimelineStore((s) => s.setViewRange);

  const rafRef = useRef<number>(0);
  const lastTimeRef = useRef<number>(0);

  // Playback loop: when the playhead crosses the middle of the view range, auto-scroll viewRange
  useEffect(() => {
    if (!isPlaying) return;

    lastTimeRef.current = performance.now();

    const tick = (now: number) => {
      const dt = (now - lastTimeRef.current) / 1000;
      lastTimeRef.current = now;

      const state = useQualityTimelineStore.getState();
      const next = state.playheadSec + dt;
      if (next >= durationSec) {
        setPlayheadSec(durationSec);
        setIsPlaying(false);
        return;
      }
      setPlayheadSec(next);

      // viewRange auto-follow: scroll when the playhead crosses the middle of the view range
      const { from, to } = state.viewRange;
      const span = to - from;
      const center = from + span / 2;
      if (next > center && to < durationSec) {
        const newFrom = Math.min(durationSec - span, next - span / 2);
        setViewRange({ from: Math.max(0, newFrom), to: Math.min(durationSec, newFrom + span) });
      }

      rafRef.current = requestAnimationFrame(tick);
    };

    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [isPlaying, durationSec, setPlayheadSec, setIsPlaying, setViewRange]);

  const togglePlay = useCallback(() => {
    if (playheadSec >= durationSec) setPlayheadSec(0);
    setIsPlaying(!isPlaying);
  }, [isPlaying, playheadSec, durationSec, setIsPlaying, setPlayheadSec]);

  const stepFrame = useCallback(
    (dir: 1 | -1) => {
      setPlayheadSec(Math.max(0, Math.min(durationSec, playheadSec + FRAME_STEP * dir)));
    },
    [playheadSec, durationSec, setPlayheadSec],
  );

  const jump = useCallback(
    (dir: 1 | -1) => {
      setPlayheadSec(Math.max(0, Math.min(durationSec, playheadSec + JUMP_STEP * dir)));
    },
    [playheadSec, durationSec, setPlayheadSec],
  );

  const zoom = useCallback(
    (dir: "in" | "out") => {
      const center = (viewRange.from + viewRange.to) / 2;
      const halfSpan = (viewRange.to - viewRange.from) / 2;
      const newHalf = dir === "in" ? halfSpan * ZOOM_FACTOR : halfSpan / ZOOM_FACTOR;
      const clampedHalf = Math.max(MIN_VIEW_RANGE / 2, Math.min(durationSec / 2, newHalf));
      setViewRange({
        from: Math.max(0, center - clampedHalf),
        to: Math.min(durationSec, center + clampedHalf),
      });
    },
    [viewRange, durationSec, setViewRange],
  );

  // Seek-bar click: if playing, pause → seek → resume
  const handleSeekClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      const rect = e.currentTarget.getBoundingClientRect();
      const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
      const wasPlaying = useQualityTimelineStore.getState().isPlaying;
      if (wasPlaying) setIsPlaying(false);
      setPlayheadSec(ratio * durationSec);
      if (wasPlaying) setIsPlaying(true);
    },
    [durationSec, setPlayheadSec, setIsPlaying],
  );

  if (durationSec <= 0) return null;

  const playheadPct = (playheadSec / durationSec) * 100;

  return (
    <div className="shrink-0 border-t border-border bg-background px-3 py-2 space-y-1.5">
      {/* Row 1: minimap (range selector) */}
      <Minimap data={data} />

      {/* Row 2: seek bar */}
      <div className="relative h-3 cursor-pointer rounded-full bg-muted/40" onClick={handleSeekClick}>
        <div className="absolute top-0 h-full w-0.5 bg-foreground" style={{ left: `${playheadPct}%` }} />
      </div>

      {/* Row 3: control buttons (centered)
       *   - Left: time display
       *   - Center: frame/jump + large play button
       *   - Right: zoom
       */}
      <div className="flex items-center gap-2">
        {/* Left: time */}
        <span className="w-32 shrink-0 text-xs tabular-nums text-muted-foreground">
          {formatDuration(playheadSec)} / {formatDuration(durationSec)}
        </span>

        {/* Center: playback controls */}
        <div className="flex flex-1 items-center justify-center gap-1.5">
          <ControlButton onClick={() => jump(-1)} title="-5s">
            <ChevronFirst size={15} />
          </ControlButton>
          <ControlButton onClick={() => stepFrame(-1)} title="-1 frame">
            <ChevronLeft size={15} />
          </ControlButton>
          <PlayPauseButton isPlaying={isPlaying} onClick={togglePlay} />
          <ControlButton onClick={() => stepFrame(1)} title="+1 frame">
            <ChevronRight size={15} />
          </ControlButton>
          <ControlButton onClick={() => jump(1)} title="+5s">
            <ChevronLast size={15} />
          </ControlButton>
        </div>

        {/* Right: zoom */}
        <div className="flex w-32 shrink-0 items-center justify-end gap-1">
          <ControlButton onClick={() => zoom("out")} title="Zoom out">
            <ZoomOut size={14} />
          </ControlButton>
          <ControlButton onClick={() => zoom("in")} title="Zoom in">
            <ZoomIn size={14} />
          </ControlButton>
        </div>
      </div>
    </div>
  );
}
