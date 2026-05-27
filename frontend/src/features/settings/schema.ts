/** Validation schema for the task-name input. */

import * as v from "valibot";

export const settingsSchema = v.object({
  taskName: v.pipe(
    v.string(),
    v.trim(),
    v.minLength(1, "Please enter a task name"),
    v.regex(/^[a-zA-Z0-9_-]+$/, "Only letters, digits, hyphens, and underscores are allowed"),
  ),
});
