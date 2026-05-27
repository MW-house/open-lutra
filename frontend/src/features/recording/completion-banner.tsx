/** Latest-record banner: persistent reference to the most recent recording, with navigation to its detail page and a dismiss button. */

import { useNavigate } from "@tanstack/react-router";
import { ArrowRight, FolderOpen, X } from "lucide-react";
import { formatDuration, formatSize } from "@/lib/format";
import { useRecordingStore } from "./store";

export function RecordingCompletionBanner() {
  const navigate = useNavigate();
  const finished = useRecordingStore((s) => s.finishedRecording);
  const dismiss = useRecordingStore((s) => s.dismissFinishedRecording);

  if (!finished) return null;

  const meta: string[] = [formatDuration(finished.durationSec)];
  if (finished.messageCount != null) meta.push(`${finished.messageCount.toLocaleString()} msgs`);
  if (finished.topicCount != null) meta.push(`${finished.topicCount} topics`);
  if (finished.size > 0) meta.push(formatSize(finished.size));

  return (
    <div className="flex items-center gap-3 border-b border-emerald-500/20 bg-emerald-500/10 px-4 py-2 text-[13px] text-emerald-300">
      <div className="flex min-w-0 flex-1 items-center gap-3">
        <span className="font-medium text-emerald-200">Latest record</span>
        <button
          type="button"
          onClick={() => navigate({ to: "/recordings/$folder", params: { folder: encodeURIComponent(finished.path) } })}
          className="flex items-center gap-1 truncate font-mono text-emerald-300 hover:text-emerald-200 hover:underline"
          title={finished.path}
        >
          <span className="truncate">{finished.name}</span>
          <FolderOpen size={12} className="flex-none" />
        </button>
        <span className="text-emerald-400/70">{meta.join(" · ")}</span>
      </div>
      <button
        type="button"
        onClick={() => navigate({ to: "/recordings/$folder", params: { folder: encodeURIComponent(finished.path) } })}
        className="flex items-center gap-1.5 rounded-md border border-emerald-500/30 px-2.5 py-1 text-emerald-200 hover:bg-emerald-500/10"
      >
        Open details
        <ArrowRight size={13} />
      </button>
      <button
        type="button"
        onClick={dismiss}
        aria-label="Close"
        className="rounded p-1 text-emerald-400/70 hover:bg-emerald-500/10 hover:text-emerald-200"
      >
        <X size={14} />
      </button>
    </div>
  );
}
