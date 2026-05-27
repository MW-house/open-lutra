/** Adaptive Detail: displays the Loss Rate graph and (when a topic is selected) Message Ticks.
 *
 * - Loss Rate line chart: always displayed (uses bin data only, no extra API)
 * - Message Ticks (Rug Plot): only displayed when a topic is selected in the Timeline
 */

import { BarChart3, ScanLine } from "lucide-react";
import type { TimelineData } from "@/api/generated/schemas";
import { useQualityTimelineStore } from "../store";
import { LossRateChart } from "./loss-rate-chart";
import { RugPlot } from "./rug-plot";

export function AdaptiveDetail({ data, selectedFolder }: { data: TimelineData; selectedFolder: string }) {
  const selectedTopic = useQualityTimelineStore((s) => s.selectedTopic);

  return (
    <div className="space-y-4">
      {/* Loss Rate: always visible */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <BarChart3 size={14} className="text-muted-foreground" />
          <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Loss Rate</span>
        </div>
        <LossRateChart data={data} />
      </div>

      {/* Message Ticks: only visible when a topic is selected */}
      {selectedTopic && (
        <div>
          <div className="flex items-center gap-2 mb-2">
            <ScanLine size={14} className="text-muted-foreground" />
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Message Ticks</span>
          </div>
          <RugPlot selectedFolder={selectedFolder} />
        </div>
      )}
    </div>
  );
}
