import { describe, expect, it } from "vitest";
import { shortMsgType } from "../quality-utils";

describe("shortMsgType", () => {
  it("shortens a ROS2 message type to its last segment", () => {
    expect(shortMsgType("sensor_msgs/msg/JointState")).toBe("JointState");
  });

  it("returns the input unchanged when there is no slash", () => {
    expect(shortMsgType("String")).toBe("String");
  });

  it("returns an empty string for empty input", () => {
    expect(shortMsgType("")).toBe("");
  });
});
