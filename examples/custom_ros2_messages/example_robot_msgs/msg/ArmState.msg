# Per-arm state that wraps a sensor_msgs/JointState.
#
# OpenLUTRA picks up the nested pattern automatically: when decoded.position is
# absent, extract_joint_positions() walks decoded.joint_state.position.

std_msgs/Header header
sensor_msgs/JointState joint_state
