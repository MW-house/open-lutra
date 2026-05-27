/** Hook that returns the list of recording folders as `FileEntry[]`.
 *
 * Thin wrapper that returns the `useFiles` TanStack Query cache as-is.
 * The backend (`scan_output_dir`) already returns a filtered and sorted list
 * of recording folders, so no further transformation is needed on the UI side.
 */

import type { FileEntry } from "@/api/generated/schemas";
import { useFiles } from "@/hooks/use-api";

export function useFileEntries(): FileEntry[] {
  const { data: files } = useFiles();
  return files?.entries ?? [];
}
