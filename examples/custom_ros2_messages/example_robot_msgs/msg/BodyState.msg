# Composite body state bundling two JointState groups on one topic.
#
# OpenLUTRA concatenates joint_state.position and neck_joint_state.position in
# declaration order, so a single subscription yields all joints in a stable
# layout. Useful when one publisher exposes coordinated joint groups
# (e.g. arm + neck).

std_msgs/Header header
sensor_msgs/JointState joint_state
sensor_msgs/JointState neck_joint_state
