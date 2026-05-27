/** Utility that safely wraps setTimeout/clearTimeout. */
export function createTimer() {
  let id: ReturnType<typeof setTimeout> | null = null;
  return {
    set(fn: () => void, ms: number) {
      if (id) clearTimeout(id);
      id = setTimeout(() => {
        id = null;
        fn();
      }, ms);
    },
    clear() {
      if (id) {
        clearTimeout(id);
        id = null;
      }
    },
  };
}
