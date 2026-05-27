/** Resolve axis and grid colors for canvas charts (uPlot, etc.) from theme CSS variables.
 *
 * Returns `--muted-foreground` for axis lines / tick labels (matching other muted text),
 * and `--border` (the subtle divider color) for grid lines. Intended to be called each
 * time a chart is created so the result follows theme switches.
 */
export function getChartAxisColors(): { axis: string; grid: string } {
  const style = getComputedStyle(document.documentElement);
  return {
    axis: style.getPropertyValue("--muted-foreground").trim() || "#999",
    grid: style.getPropertyValue("--border").trim() || "#333",
  };
}
