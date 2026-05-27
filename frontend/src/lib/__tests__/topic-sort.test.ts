import { describe, expect, it } from "vitest";
import { getTopicCategory, sortTopicsByCategory } from "../topic-sort";

describe("getTopicCategory", () => {
  it("returns image when msg_type contains 'Image'", () => {
    expect(getTopicCategory("sensor_msgs/msg/Image")).toBe("image");
    expect(getTopicCategory("sensor_msgs/msg/CompressedImage")).toBe("image");
  });

  it("returns other when 'Image' is not present", () => {
    expect(getTopicCategory("sensor_msgs/msg/JointState")).toBe("other");
    expect(getTopicCategory("custom_msgs/msg/ArmSlaveData")).toBe("other");
  });

  it("treats null/undefined/empty string as other", () => {
    expect(getTopicCategory(null)).toBe("other");
    expect(getTopicCategory(undefined)).toBe("other");
    expect(getTopicCategory("")).toBe("other");
  });
});

describe("sortTopicsByCategory", () => {
  type T = { name: string; type: string };

  it("places images on top and joint (other) below", () => {
    const topics: T[] = [
      { name: "/joint_states", type: "sensor_msgs/msg/JointState" },
      { name: "/cam0/image", type: "sensor_msgs/msg/CompressedImage" },
    ];
    const sorted = sortTopicsByCategory(
      topics,
      (t) => t.name,
      (t) => t.type,
    );
    expect(sorted.map((t) => t.name)).toEqual(["/cam0/image", "/joint_states"]);
  });

  it("sorts alphabetically within each category", () => {
    const topics: T[] = [
      { name: "/zebra_cam", type: "sensor_msgs/msg/Image" },
      { name: "/alpha_cam", type: "sensor_msgs/msg/Image" },
      { name: "/zebra_joint", type: "sensor_msgs/msg/JointState" },
      { name: "/alpha_joint", type: "sensor_msgs/msg/JointState" },
    ];
    const sorted = sortTopicsByCategory(
      topics,
      (t) => t.name,
      (t) => t.type,
    );
    expect(sorted.map((t) => t.name)).toEqual(["/alpha_cam", "/zebra_cam", "/alpha_joint", "/zebra_joint"]);
  });

  it("does not mutate the input array", () => {
    const topics: T[] = [
      { name: "/b", type: "sensor_msgs/msg/JointState" },
      { name: "/a", type: "sensor_msgs/msg/Image" },
    ];
    const original = [...topics];
    sortTopicsByCategory(
      topics,
      (t) => t.name,
      (t) => t.type,
    );
    expect(topics).toEqual(original);
  });

  it("returns an empty array when given an empty array", () => {
    expect(
      sortTopicsByCategory(
        [],
        (t: T) => t.name,
        (t) => t.type,
      ),
    ).toEqual([]);
  });

  it("places custom message types on the joint side", () => {
    const topics: T[] = [
      { name: "/mcap/body", type: "custom_msgs/msg/BodyData" },
      { name: "/cam/image", type: "sensor_msgs/msg/CompressedImage" },
    ];
    const sorted = sortTopicsByCategory(
      topics,
      (t) => t.name,
      (t) => t.type,
    );
    expect(sorted.map((t) => t.name)).toEqual(["/cam/image", "/mcap/body"]);
  });
});
