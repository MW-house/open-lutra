/** Helper functions for the quality summary view. */

/** Shorten a message type name (e.g. sensor_msgs/msg/JointState → JointState). */
export function shortMsgType(msgType: string): string {
  const parts = msgType.split("/");
  return parts[parts.length - 1];
}
