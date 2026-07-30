/** Helpers for master-defined recording metadata fields. */

/**
 * Key of the task-evaluation field. It is a post-recording judgement, so — as an
 * MW-specific special case — it is hidden from the pre-recording metadata panel
 * and entered from the recording-completion banner instead, defaulting to
 * {@link TASK_EVALUATION_DEFAULT}. The field itself is still master-defined, so
 * its label and options come from the active config's `metadata_fields`.
 */
export const TASK_EVALUATION_KEY = "task_evaluation";

/** Default value for {@link TASK_EVALUATION_KEY} (success). */
export const TASK_EVALUATION_DEFAULT = "success";

/**
 * Whether `value` satisfies the field's regex `pattern`.
 *
 * An empty value, an absent pattern, and a malformed (uncompilable) pattern all
 * count as valid: empty means "not entered yet" and a bad config-provided regex
 * should not trap the operator.
 */
export function matchesPattern(pattern: string | null | undefined, value: string): boolean {
  if (!pattern || value === "") return true;
  try {
    return new RegExp(pattern).test(value);
  } catch {
    return true;
  }
}
