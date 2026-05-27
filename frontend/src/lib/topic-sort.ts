/** Unified topic ordering utility.
 *
 * Across every page, topics are sorted by the same rule: "image topics on top,
 * joint (other) topics below, alphabetical within each category". The category is
 * determined by whether the msg_type string contains "Image":
 *
 * - sensor_msgs/msg/CompressedImage / sensor_msgs/msg/Image → treated as image
 * - Custom message types (vendor-specific or user-defined) → treated as joint
 * - Anything else → treated as joint
 *
 * The backend's structure-based detection (`_is_image_message`) inspects the
 * message's format/data fields, but the frontend has no access to message
 * contents, so we classify by type-name string instead. Custom message types
 * do not contain "Image" in their type names, so they fall on the joint side.
 */

/** Which category a topic belongs to (image / other = joint). */
export type TopicCategory = "image" | "other";

/** Determine the category from a msg_type string. */
export function getTopicCategory(msgType: string | undefined | null): TopicCategory {
  if (!msgType) return "other";
  return msgType.includes("Image") ? "image" : "other";
}

/** Category order (image = 0, other = 1). Used as a sort key. */
function categoryRank(msgType: string | undefined | null): number {
  return getTopicCategory(msgType) === "image" ? 0 : 1;
}

/** Sort a topic array as "image on top, joint below, alphabetical within each category".
 *
 * Does not mutate the input array (returns a new one). The caller supplies an
 * accessor for msg_type and an accessor for the topic name.
 */
export function sortTopicsByCategory<T>(
  topics: readonly T[],
  getName: (item: T) => string,
  getMsgType: (item: T) => string | undefined | null,
): T[] {
  return [...topics].sort((a, b) => {
    const rankDiff = categoryRank(getMsgType(a)) - categoryRank(getMsgType(b));
    if (rankDiff !== 0) return rankDiff;
    return getName(a).localeCompare(getName(b));
  });
}
