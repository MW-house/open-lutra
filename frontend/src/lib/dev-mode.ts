/** Dev mode check: returns true only when `VITE_DEV_MODE=true` is set.
 *
 * Independent from Vite's native `import.meta.env.DEV` (which is always true under
 * the vite dev server). Used to gate developer-only UI that is only enabled via
 * `make dev-up`.
 */
export function isDevMode(): boolean {
  return import.meta.env.VITE_DEV_MODE === "true";
}
