/** Latest-record banner: persistent reference to the most recent recording, with a task-evaluation
 * selector (a post-recording judgement, defaulting to success), navigation to its detail page, a
 * delete action, and a dismiss button. */

import { useNavigate } from "@tanstack/react-router";
import { ArrowRight, ChevronDown, FolderOpen, Loader2, Trash2, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { useConfig, useDeleteRecordings, useFiles, useUpdateRecordingMeta } from "@/hooks/use-api";
import { useAddLog } from "@/hooks/use-topics-stream";
import { formatDuration, formatSize } from "@/lib/format";
import { TASK_EVALUATION_DEFAULT, TASK_EVALUATION_KEY } from "@/lib/metadata-field";
import { toast } from "@/stores/toast-store";
import { useRecordingStore } from "./store";
import { useEvaluationShortcut } from "./use-evaluation-shortcut";

export function RecordingCompletionBanner() {
  const navigate = useNavigate();

  // --- Render-only state (drives the queries below, so read first) ---
  const finished = useRecordingStore((s) => s.finishedRecording);
  const dismiss = useRecordingStore((s) => s.dismissFinishedRecording);

  // --- Server state ---
  // task_evaluation is master-defined (label + options) but entered here instead of pre-recording.
  const { data: config } = useConfig();
  const evalField = config?.metadata_fields.find((f) => f.key === TASK_EVALUATION_KEY);
  // The just-finished recording carries the pre-recording metadata; the full map is needed so a
  // PATCH of task_evaluation does not drop the other fields.
  const { data: files } = useFiles({ enabled: !!finished });
  const entry = files?.entries.find((e) => e.name === finished?.name);
  const storedEvaluation = entry?.metadata[TASK_EVALUATION_KEY];

  const deleteMutation = useDeleteRecordings();
  const updateMeta = useUpdateRecordingMeta();
  const { mutate: mutateMeta } = updateMeta;
  const addLog = useAddLog();

  // --- Side effects ---
  // Optimistic override so the selector reflects a change before the recordings list refetches.
  // Scoped to a recording name so a stale value never bleeds into the next recording's banner.
  const [override, setOverride] = useState<{ name: string; value: string } | null>(null);

  // Persist the default (success) once per recording so an untouched banner still labels the take.
  const seededName = useRef<string | null>(null);
  useEffect(() => {
    if (!finished || !evalField || !entry || storedEvaluation || seededName.current === finished.name) return;
    seededName.current = finished.name;
    mutateMeta({
      name: finished.name,
      data: { metadata: { ...entry.metadata, [TASK_EVALUATION_KEY]: TASK_EVALUATION_DEFAULT } },
    });
  }, [finished, evalField, entry, storedEvaluation, mutateMeta]);

  // Persist a task-evaluation change, merging over the recording's existing metadata so the
  // pre-recording fields survive the whole-map PATCH. Hoisted above the early return so the
  // keyboard shortcut can reuse it.
  const saveEvaluation = (next: string) => {
    if (!finished || !entry) return;
    setOverride({ name: finished.name, value: next });
    updateMeta.mutate(
      { name: finished.name, data: { metadata: { ...entry.metadata, [TASK_EVALUATION_KEY]: next } } },
      {
        onError: (err: unknown) => {
          const msg = err instanceof Error ? err.message : "Update failed";
          addLog("danger", `Failed to update task evaluation (${finished.name}): ${msg}`);
          toast.error("Metadata update failed", msg);
        },
      },
    );
  };

  // The selector's current value, also the value the keyboard shortcut cycles from.
  const currentEvaluation =
    (override?.name === finished?.name ? override?.value : undefined) ?? storedEvaluation ?? TASK_EVALUATION_DEFAULT;

  // Keyboard shortcut: E cycles the evaluation without reaching for the mouse. Gated on the same
  // conditions as the selector (a save in flight disables both).
  useEvaluationShortcut({
    enabled: !!finished && !!evalField && !!entry && !updateMeta.isPending,
    options: evalField?.options ?? [],
    current: currentEvaluation,
    onSelect: saveEvaluation,
  });

  if (!finished) return null;

  const meta: string[] = [formatDuration(finished.durationSec)];
  if (finished.messageCount != null) meta.push(`${finished.messageCount.toLocaleString()} msgs`);
  if (finished.topicCount != null) meta.push(`${finished.topicCount} topics`);
  if (finished.size > 0) meta.push(formatSize(finished.size));

  // --- Event handlers ---
  const handleDelete = () =>
    deleteMutation.mutate(
      { data: { folders: [finished.name] } },
      {
        onSuccess: () => {
          addLog("info", `Deleted recording: ${finished.name}`);
          toast.success("Recording deleted", finished.name);
          dismiss();
        },
        onError: (err: unknown) => {
          const msg = err instanceof Error ? err.message : "Delete failed";
          addLog("danger", `Delete failed: ${msg}`);
          toast.error("Delete failed", msg);
        },
      },
    );

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

      {/* Task evaluation (post-recording judgement), defaulting to success. */}
      {evalField && (
        <label className="flex flex-none items-center gap-1.5 text-emerald-200">
          <span className="whitespace-nowrap">{evalField.label}</span>
          <div className="relative">
            <select
              value={currentEvaluation}
              disabled={!entry || updateMeta.isPending}
              onChange={(e) => saveEvaluation(e.target.value)}
              className="appearance-none rounded-md border border-emerald-500/30 bg-transparent py-1 pr-6 pl-2 text-[13px] text-emerald-100 cursor-pointer focus:outline-none focus:ring-1 focus:ring-emerald-400/50 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {evalField.options.map((opt) => (
                <option key={opt.value} value={opt.value} className="bg-background text-foreground">
                  {opt.label}
                </option>
              ))}
            </select>
            <ChevronDown
              size={13}
              className="pointer-events-none absolute top-1/2 right-1.5 -translate-y-1/2 text-emerald-300"
            />
          </div>
          {/* Hint for the keyboard shortcut that cycles the value (see use-evaluation-shortcut). */}
          <kbd
            title="Eキーで切り替え"
            className="flex-none rounded border border-emerald-500/30 px-1.5 py-0.5 font-mono text-[13px] text-emerald-300/70 leading-none"
          >
            E
          </kbd>
        </label>
      )}

      {/* Discard the recording that was just made (e.g. a bad take), with confirmation. */}
      <AlertDialog>
        <AlertDialogTrigger asChild>
          <button
            type="button"
            disabled={deleteMutation.isPending}
            className="flex flex-none items-center gap-1.5 rounded-md border border-emerald-500/30 px-2.5 py-1 text-emerald-200 hover:border-red-500/40 hover:bg-red-500/10 hover:text-red-300 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {deleteMutation.isPending ? <Loader2 size={13} className="animate-spin" /> : <Trash2 size={13} />}
            Delete
          </button>
        </AlertDialogTrigger>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete recording</AlertDialogTitle>
            <AlertDialogDescription>Delete "{finished.name}"? This action cannot be undone.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel asChild>
              <Button variant="outline" size="sm">
                Cancel
              </Button>
            </AlertDialogCancel>
            <AlertDialogAction asChild>
              <Button variant="destructive" size="sm" onClick={handleDelete}>
                Delete
              </Button>
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <button
        type="button"
        onClick={() => navigate({ to: "/recordings/$folder", params: { folder: encodeURIComponent(finished.path) } })}
        className="flex flex-none items-center gap-1.5 rounded-md border border-emerald-500/30 px-2.5 py-1 text-emerald-200 hover:bg-emerald-500/10"
      >
        Open details
        <ArrowRight size={13} />
      </button>
      <button
        type="button"
        onClick={dismiss}
        aria-label="Close"
        className="flex-none rounded p-1 text-emerald-400/70 hover:bg-emerald-500/10 hover:text-emerald-200"
      >
        <X size={14} />
      </button>
    </div>
  );
}
