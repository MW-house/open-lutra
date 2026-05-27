/** Collapsed view of the Topics sidebar: shows only an expand button. */

import { PanelLeftOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { usePanelStore } from "@/stores/panel-store";

export function TopicsRail() {
  const toggleTopicsSidebar = usePanelStore((s) => s.toggleTopicsSidebar);

  return (
    <div className="flex h-full w-10 flex-col items-center gap-2 border-r border-border bg-background py-2">
      <Tooltip>
        <TooltipTrigger asChild>
          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={toggleTopicsSidebar}>
            <PanelLeftOpen size={14} />
          </Button>
        </TooltipTrigger>
        <TooltipContent side="right">Show Topics</TooltipContent>
      </Tooltip>
    </div>
  );
}
