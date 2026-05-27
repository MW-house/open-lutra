/** LiveTopics: live quality monitoring and preview for ROS2 topics (left panels of the recording page). */

import { useTopicStats } from "@/hooks/use-topics-stream";
import { usePanelStore } from "@/stores/panel-store";
import { useLiveTopicsStore } from "./store";
import { PreviewPane } from "./ui/preview-pane";
import { TopicList } from "./ui/topic-list";
import { TopicsRail } from "./ui/topics-rail";

/** Topic list panel. Renders a narrow rail when the sidebar is collapsed. */
export function LiveTopics() {
  const topicsSidebarOpen = usePanelStore((s) => s.topicsSidebarOpen);

  if (!topicsSidebarOpen) {
    return <TopicsRail />;
  }
  return (
    <div className="flex h-full flex-col bg-background">
      <TopicList />
    </div>
  );
}

/** PREVIEW panel. Displays previewed topics in a grid, or a placeholder when none are selected. */
export function LiveTopicPreview() {
  const previewedTopics = useLiveTopicsStore((state) => state.previewedTopics);
  const topicStats = useTopicStats();

  // Resolve TopicInfo in previewedTopics order (= selection order). Excludes ones not yet in SSE stats.
  const previewedData = previewedTopics
    .map((name) => topicStats.find((t) => t.name === name))
    .filter((t): t is (typeof topicStats)[number] => t !== undefined);

  return <PreviewPane previewedTopics={previewedData} />;
}
