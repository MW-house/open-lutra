/** Operator alert pinned to the top center of the recorder page, asking the operator to call an
 * administrator when required topics stop delivering data. Stays until the operator acknowledges it;
 * see `../topic-failure.ts` for the detection rules. */

import { TriangleAlert } from "lucide-react";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { useConfig } from "@/hooks/use-api";
import { useTopicStats } from "@/hooks/use-topics-stream";
import { acknowledgeTopicFailures, initialTopicFailureState, nextTopicFailureState } from "../topic-failure";

export function TopicFailureAlert() {
  // --- Server state ---
  const { data: config } = useConfig();
  const defaultTopics = config?.default_topics;

  // --- Streaming ---
  const topicStats = useTopicStats();

  // --- Side effects ---
  const [state, setState] = useState(initialTopicFailureState);
  useEffect(() => {
    if (!defaultTopics) return;
    setState((prev) => nextTopicFailureState(prev, defaultTopics, topicStats, Date.now()));
  }, [defaultTopics, topicStats]);

  if (state.alerted.length === 0) return null;

  return (
    <div className="pointer-events-none fixed inset-0 z-50 flex justify-center px-4 pt-16">
      {/* Flashing red wash + thick edge so the alert is caught in peripheral vision; clicks pass through. */}
      <div className="absolute inset-0 animate-[alert-flash_1s_ease-in-out_infinite] bg-red-600 shadow-[inset_0_0_0_12px_rgb(220,38,38)]" />
      <div
        role="alert"
        className="pointer-events-auto relative h-fit w-full max-w-xl animate-[alert-blink_1s_ease-in-out_infinite] rounded-lg border-2 border-red-300 bg-red-600 px-6 py-4 text-white shadow-2xl"
      >
        <div className="flex items-center gap-3">
          <TriangleAlert className="size-8 shrink-0" />
          <div className="text-xl font-bold">管理者を呼んでください</div>
        </div>
        <p className="mt-2 text-[14px]">データ取得に失敗しているトピックがあります。</p>
        <ul className="mt-2 space-y-0.5 rounded bg-red-700/60 px-3 py-2 font-mono text-[13px]">
          {state.alerted.map((topic) => (
            <li key={topic}>
              {topic}
              {!state.failing.includes(topic) && <span className="ml-2 font-sans text-red-100">(復旧済み)</span>}
            </li>
          ))}
        </ul>
        <div className="mt-3 flex justify-end">
          <Button
            variant="secondary"
            className="bg-white text-red-700 hover:bg-red-50"
            onClick={() => setState(acknowledgeTopicFailures)}
          >
            確認
          </Button>
        </div>
      </div>
    </div>
  );
}
