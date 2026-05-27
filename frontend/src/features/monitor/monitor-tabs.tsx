/** Monitor tabs: switches between the Loss Rate chart (default) and Log views. */

import { Activity, ScrollText } from "lucide-react";
import { type BottomTab, usePanelStore } from "@/stores/panel-store";
import { LogViewer } from "./log-viewer";
import { LossRateChart } from "./loss-rate-chart";

const tabs: { id: BottomTab; label: string; icon: React.ReactNode }[] = [
  { id: "loss-rate", label: "Loss Rate", icon: <Activity size={13} /> },
  { id: "log", label: "Log", icon: <ScrollText size={13} /> },
];

export function MonitorTabs() {
  const activeTab = usePanelStore((state) => state.bottomTab);
  const setTab = usePanelStore((state) => state.setBottomTab);

  return (
    <div className="flex h-full flex-col bg-background">
      {/* Tab header */}
      <div className="flex items-center border-b border-border">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            className={`flex items-center gap-1.5 px-3 py-1.5 text-sm font-semibold uppercase tracking-wider transition-colors ${
              activeTab === tab.id
                ? "text-foreground border-b-2 border-foreground"
                : "text-muted-foreground hover:text-foreground/70"
            }`}
            onClick={() => setTab(tab.id)}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-hidden">{activeTab === "loss-rate" ? <LossRateChart /> : <LogViewer />}</div>
    </div>
  );
}
