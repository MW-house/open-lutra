/** Detection of required topics whose data has stopped arriving, for the "call an administrator" alert.
 *
 * A required topic (config `default_topics`) is failing when no message has arrived for
 * TOPIC_FAILURE_THRESHOLD_SEC: measured by the backend (`silent_sec`) for subscribed topics, and by
 * the frontend for topics absent from the stream (not discovered on DDS at all). Topics the operator
 * deselected are not monitored, so they never fail.
 *
 * An alerted topic stays latched until the operator acknowledges it. An acknowledged topic does not
 * re-alert while it keeps failing; it alerts again only after it recovers and fails anew. */

import type { TopicInfo } from "@/api/generated/schemas";

export const TOPIC_FAILURE_THRESHOLD_SEC = 10;

export interface TopicFailureState {
  /** Topics shown in the alert, in the order they started failing. */
  alerted: string[];
  /** Topics failing as of the latest tick (an alerted topic absent here has recovered). */
  failing: string[];
  /** Failing topics the operator has already acknowledged. */
  acknowledged: string[];
  /** Epoch ms at which each required topic was first seen absent from the stream. */
  missingSinceMs: Record<string, number>;
}

export const initialTopicFailureState: TopicFailureState = {
  alerted: [],
  failing: [],
  acknowledged: [],
  missingSinceMs: {},
};

/** Advance the state by one topic-stats tick. */
export function nextTopicFailureState(
  prev: TopicFailureState,
  requiredTopics: string[],
  stats: TopicInfo[],
  nowMs: number,
): TopicFailureState {
  const byName = new Map(stats.map((t) => [t.name, t]));
  const missingSinceMs: Record<string, number> = {};
  const failing: string[] = [];

  for (const name of requiredTopics) {
    const topic = byName.get(name);
    if (topic) {
      if (topic.is_subscribed && topic.silent_sec >= TOPIC_FAILURE_THRESHOLD_SEC) failing.push(name);
      continue;
    }
    const since = prev.missingSinceMs[name] ?? nowMs;
    missingSinceMs[name] = since;
    if (nowMs - since >= TOPIC_FAILURE_THRESHOLD_SEC * 1000) failing.push(name);
  }

  const acknowledged = prev.acknowledged.filter((name) => failing.includes(name));
  const newlyAlerted = failing.filter((name) => !prev.alerted.includes(name) && !acknowledged.includes(name));
  return { alerted: [...prev.alerted, ...newlyAlerted], failing, acknowledged, missingSinceMs };
}

/** Dismiss the alert; topics still failing stay suppressed until they recover. */
export function acknowledgeTopicFailures(prev: TopicFailureState): TopicFailureState {
  return { ...prev, alerted: [], acknowledged: [...new Set([...prev.acknowledged, ...prev.alerted])] };
}
