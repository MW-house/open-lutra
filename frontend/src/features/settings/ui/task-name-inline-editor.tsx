/** Inline task-name editor that lives in the recording bar header.
 *
 * Displays the current task name with a pencil icon. When unset, shows a
 * "Set task name" placeholder that still opens the editor on click. Click
 * the pencil (or double-click the text) to switch to edit mode. In edit
 * mode, Enter / blur commits, Escape cancels. Invalid input (empty or
 * disallowed characters) leaves the value untouched.
 *
 * Edit mode also shows a small autocomplete dropdown of previously-used
 * task names (most-recently-used first), filtered by the current draft.
 * Arrow up/down navigates suggestions, Enter selects the highlighted one
 * (or commits the typed value if nothing is highlighted), Tab also selects.
 */

import { Pencil } from "lucide-react";
import type { KeyboardEvent } from "react";
import { useEffect, useMemo, useRef, useState } from "react";
import * as v from "valibot";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useTaskNames } from "@/hooks/use-api";
import { settingsSchema } from "../schema";
import { useSettingsStore } from "../store";

/** Top N suggestions shown in the dropdown. */
const MAX_SUGGESTIONS = 8;

export function TaskNameInlineEditor() {
  const taskName = useSettingsStore((s) => s.taskName);
  const update = useSettingsStore((s) => s.update);

  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(taskName);
  const [highlightIndex, setHighlightIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);

  const allTaskNames = useTaskNames({ enabled: editing });

  // Case-insensitive substring filter against the current draft. Two
  // special cases skip the substring narrowing and show every other
  // suggestion: an empty draft, and a draft that is still equal to the
  // committed task name (i.e. the editor was just opened and the user
  // has not changed anything yet). Always exclude the literal draft so
  // the dropdown does not echo the input.
  const suggestions = useMemo(() => {
    const needle = draft.trim().toLowerCase();
    const noFilter = !needle || draft === taskName;
    const matches = noFilter
      ? allTaskNames.filter((name) => name !== draft)
      : allTaskNames.filter((name) => name.toLowerCase().includes(needle) && name !== draft);
    return matches.slice(0, MAX_SUGGESTIONS);
  }, [allTaskNames, draft, taskName]);

  useEffect(() => {
    if (editing) {
      inputRef.current?.focus();
      inputRef.current?.select();
    }
  }, [editing]);

  // Reset highlight whenever the suggestion set changes (typing narrows it).
  // The dependency is intentionally `suggestions` (not just `draft`) so a
  // late-arriving query also resets the highlight cleanly.
  // biome-ignore lint/correctness/useExhaustiveDependencies: highlight reset is driven by suggestion list identity.
  useEffect(() => {
    setHighlightIndex(-1);
  }, [suggestions]);

  const startEdit = () => {
    setDraft(taskName);
    setHighlightIndex(-1);
    setEditing(true);
  };

  const commitValue = (value: string) => {
    const result = v.safeParse(settingsSchema, { taskName: value });
    if (result.success) {
      update({ taskName: result.output.taskName });
    }
    setEditing(false);
  };

  const commit = () => commitValue(draft);

  // Dispatch table maps each navigation key to its handler. Returning true
  // means the event was consumed (preventDefault). The table keeps the
  // top-level handler trivial enough to satisfy the lint budget.
  const keyActions: Record<string, () => boolean> = {
    Enter: () => {
      const picked = highlightIndex >= 0 ? suggestions[highlightIndex] : undefined;
      commitValue(picked ?? draft);
      return true;
    },
    Escape: () => {
      setEditing(false);
      return true;
    },
    Tab: () => {
      const picked = highlightIndex >= 0 ? suggestions[highlightIndex] : undefined;
      if (!picked) return false;
      commitValue(picked);
      return true;
    },
    ArrowDown: () => {
      if (suggestions.length === 0) return false;
      setHighlightIndex((i) => (i + 1) % suggestions.length);
      return true;
    },
    ArrowUp: () => {
      if (suggestions.length === 0) return false;
      setHighlightIndex((i) => (i <= 0 ? suggestions.length - 1 : i - 1));
      return true;
    },
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    const action = keyActions[e.key];
    if (action?.()) e.preventDefault();
  };

  if (editing) {
    return (
      <span className="relative flex items-center gap-1 text-base text-muted-foreground">
        <input
          ref={inputRef}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={(e) => {
            // Skip commit when blur is caused by clicking a suggestion — the
            // suggestion's mousedown handler already calls commitValue().
            if (e.relatedTarget?.getAttribute("data-suggestion") === "true") return;
            commit();
          }}
          aria-label="Task name"
          aria-autocomplete="list"
          aria-controls={suggestions.length > 0 ? "task-name-suggestions" : undefined}
          aria-activedescendant={highlightIndex >= 0 ? `task-name-suggestion-${highlightIndex}` : undefined}
          role="combobox"
          aria-expanded={suggestions.length > 0}
          className="h-8 w-48 rounded border border-input bg-transparent px-2 text-base text-foreground outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50"
        />
        {suggestions.length > 0 && (
          <div
            id="task-name-suggestions"
            role="listbox"
            aria-label="Task name suggestions"
            className="absolute left-0 top-9 z-50 flex max-h-60 w-48 flex-col overflow-y-auto rounded border border-border bg-popover text-base text-popover-foreground shadow-md"
          >
            {suggestions.map((name, idx) => (
              <button
                key={name}
                id={`task-name-suggestion-${idx}`}
                type="button"
                role="option"
                aria-selected={highlightIndex === idx}
                data-suggestion="true"
                onMouseDown={(e) => {
                  // Use mousedown so we beat the input's blur, which would
                  // otherwise commit the draft before this click registers.
                  e.preventDefault();
                  commitValue(name);
                }}
                onMouseEnter={() => setHighlightIndex(idx)}
                className={`w-full cursor-pointer px-2 py-1.5 text-left text-[13px] hover:bg-muted ${
                  highlightIndex === idx ? "bg-muted" : ""
                }`}
              >
                {name}
              </button>
            ))}
          </div>
        )}
      </span>
    );
  }

  return (
    <span className="flex items-center gap-1.5 text-base text-muted-foreground">
      <span
        onDoubleClick={startEdit}
        title="Double-click to edit"
        className={
          taskName
            ? "cursor-text select-none rounded px-1 font-medium text-foreground hover:bg-muted/60"
            : "cursor-text select-none rounded px-1 italic text-muted-foreground hover:bg-muted/60"
        }
      >
        {taskName || "Set task name"}
      </span>
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            type="button"
            onClick={startEdit}
            aria-label="Edit task name"
            className="flex h-6 w-6 items-center justify-center rounded text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            <Pencil size={14} />
          </button>
        </TooltipTrigger>
        <TooltipContent side="bottom">Edit task name</TooltipContent>
      </Tooltip>
    </span>
  );
}
