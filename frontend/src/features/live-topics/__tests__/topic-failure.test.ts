import { describe, expect, it } from "vitest";
import type { TopicInfo } from "@/api/generated/schemas";
import {
  acknowledgeTopicFailures,
  initialTopicFailureState,
  nextTopicFailureState,
  TOPIC_FAILURE_THRESHOLD_SEC,
  type TopicFailureState,
} from "../topic-failure";

const topic = (name: string, silentSec: number, isSubscribed = true): TopicInfo => ({
  name,
  msg_type: "sensor_msgs/msg/JointState",
  actual_hz: 0,
  status: "danger",
  message_count: 0,
  is_subscribed: isSubscribed,
  baseline_hz: null,
  baseline_fixed: false,
  loss_rate: 0,
  drop_count: 0,
  continuity_score: 1,
  qos_reliability: "RELIABLE",
  silent_sec: silentSec,
});

const T = TOPIC_FAILURE_THRESHOLD_SEC;

describe("nextTopicFailureState", () => {
  it("alerts a subscribed required topic once it is silent for the threshold", () => {
    const below = nextTopicFailureState(initialTopicFailureState, ["/a"], [topic("/a", T - 0.1)], 0);
    expect(below.alerted).toEqual([]);

    const at = nextTopicFailureState(below, ["/a"], [topic("/a", T)], 0);
    expect(at.alerted).toEqual(["/a"]);
    expect(at.failing).toEqual(["/a"]);
  });

  it("ignores topics that are not required or not subscribed", () => {
    const next = nextTopicFailureState(
      initialTopicFailureState,
      ["/a"],
      [topic("/a", T * 2, false), topic("/other", T * 2)],
      0,
    );
    expect(next.alerted).toEqual([]);
  });

  it("alerts a required topic absent from the stream once it has been missing for the threshold", () => {
    const first = nextTopicFailureState(initialTopicFailureState, ["/a"], [], 1_000);
    expect(first.missingSinceMs).toEqual({ "/a": 1_000 });
    expect(first.alerted).toEqual([]);

    const later = nextTopicFailureState(first, ["/a"], [], 1_000 + T * 1000);
    expect(later.alerted).toEqual(["/a"]);
  });

  it("forgets the missing timer once the topic appears", () => {
    const missing = nextTopicFailureState(initialTopicFailureState, ["/a"], [], 0);
    const appeared = nextTopicFailureState(missing, ["/a"], [topic("/a", 0)], 1_000);
    expect(appeared.missingSinceMs).toEqual({});
  });

  it("keeps a recovered topic latched until acknowledged", () => {
    const failed = nextTopicFailureState(initialTopicFailureState, ["/a"], [topic("/a", T)], 0);
    const recovered = nextTopicFailureState(failed, ["/a"], [topic("/a", 0)], 0);
    expect(recovered.alerted).toEqual(["/a"]);
    expect(recovered.failing).toEqual([]);
  });

  it("appends newly failing topics without duplicating latched ones", () => {
    const one = nextTopicFailureState(initialTopicFailureState, ["/a", "/b"], [topic("/a", T), topic("/b", 0)], 0);
    const two = nextTopicFailureState(one, ["/a", "/b"], [topic("/a", T), topic("/b", T)], 0);
    expect(two.alerted).toEqual(["/a", "/b"]);
  });
});

describe("acknowledgeTopicFailures", () => {
  const failing: TopicFailureState = nextTopicFailureState(initialTopicFailureState, ["/a"], [topic("/a", T)], 0);

  it("clears the alert and suppresses topics that keep failing", () => {
    const acked = acknowledgeTopicFailures(failing);
    expect(acked.alerted).toEqual([]);

    const stillFailing = nextTopicFailureState(acked, ["/a"], [topic("/a", T + 5)], 0);
    expect(stillFailing.alerted).toEqual([]);
  });

  it("re-alerts a topic that recovers and then fails again", () => {
    const acked = acknowledgeTopicFailures(failing);
    const recovered = nextTopicFailureState(acked, ["/a"], [topic("/a", 0)], 0);
    expect(recovered.acknowledged).toEqual([]);

    const failedAgain = nextTopicFailureState(recovered, ["/a"], [topic("/a", T)], 0);
    expect(failedAgain.alerted).toEqual(["/a"]);
  });
});
