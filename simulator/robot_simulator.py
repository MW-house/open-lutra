"""Robot simulator for development and testing.

Publishes simulated ROS2 topics that mimic a real robot
with multiple depth cameras, allowing end-to-end testing without
physical hardware.

Published topics:
  /robot_slave/states                                       (sensor_msgs/JointState)     @ 100Hz
  /robot_master/cmd                                         (sensor_msgs/JointState)     @ 100Hz
  /right_arm_depth_cam/color/image_raw/compressed           (sensor_msgs/CompressedImage) @ 30Hz
  /right_arm_depth_cam_2/color/image_raw/compressed         (sensor_msgs/CompressedImage) @ 30Hz
  /left_arm_depth_cam/color/image_raw/compressed            (sensor_msgs/CompressedImage) @ 30Hz
  /left_arm_depth_cam_2/color/image_raw/compressed          (sensor_msgs/CompressedImage) @ 30Hz

Data sources:
  - Cameras: loops the real-recording JPEGs under `simulator/frames/<cam>/` (different
    footage per camera). The `_2` topics republish the same data as their counterpart
    so a single sample dataset can populate four independent topics — enough to exercise
    multi-camera UI paths without bundling more footage.
  - Joints: replays the real-recording trajectory (right arm) in
    `simulator/joint_replay.json` by indexing into it via elapsed time, looping at the
    end; fed to both slave and master

Simulation modes: see config.py
"""

import bisect
import json
from pathlib import Path

import rclpy
from config import SIM_MODE
from fault_modes import FaultInjector
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage, JointState
from std_msgs.msg import Header

# Frame ID shared by all cameras (matches the `frame_id` from real-hardware recordings)
CAMERA_FRAME_ID = "camera_color_optical_frame"
JOINT_FRAME_ID = "base_link"

CAMERA_TOPICS_BY_DIR: dict[str, list[str]] = {
    "right_arm": [
        "/right_arm_depth_cam/color/image_raw/compressed",
        "/right_arm_depth_cam_2/color/image_raw/compressed",
    ],
    "left_arm": [
        "/left_arm_depth_cam/color/image_raw/compressed",
        "/left_arm_depth_cam_2/color/image_raw/compressed",
    ],
}

FRAMES_DIR = Path(__file__).parent / "frames"
JOINT_REPLAY_PATH = Path(__file__).parent / "joint_replay.json"

CAMERA_HZ = 30
JOINT_HZ = 100


def _load_camera_frames() -> dict[str, list[bytes]]:
    """Load `frames/<cam>/*.jpg` for each camera dir and key by topic name.

    When a directory maps to multiple topics, the frame list is shared by reference
    across topics so the same bytes back every mirror — no extra memory.
    """
    frames: dict[str, list[bytes]] = {}
    for cam_dir, topics in CAMERA_TOPICS_BY_DIR.items():
        cam_path = FRAMES_DIR / cam_dir
        if not cam_path.is_dir():
            continue
        loaded = [p.read_bytes() for p in sorted(cam_path.glob("*.jpg"))]
        if not loaded:
            continue
        for topic in topics:
            frames[topic] = loaded
    return frames


def _load_joint_replay() -> dict | None:
    """Load joint_replay.json. Returns None if it does not exist."""
    if not JOINT_REPLAY_PATH.is_file():
        return None
    return json.loads(JOINT_REPLAY_PATH.read_text())


class RobotSimulator(Node):
    """ROS2 node that simulates robot data."""

    def __init__(self) -> None:
        super().__init__("robot_simulator")
        self.get_logger().info(f"Starting robot simulator (mode: {SIM_MODE})...")

        self._camera_frame_idx = 0
        self._joint_tick = 0  # tick count of the 100Hz timer

        # Fault injection
        self._fault = FaultInjector(
            SIM_MODE,
            log=lambda level, msg: getattr(self.get_logger(), level)(msg),
        )

        # Camera frames (per topic)
        self._camera_frames = _load_camera_frames()
        if self._camera_frames:
            counts = ", ".join(f"{t.split('/')[1]}={len(v)}" for t, v in self._camera_frames.items())
            self.get_logger().info(f"Loaded camera frames: {counts}")
        else:
            self.get_logger().warn("No camera frames found, camera topics will not be published")

        # Joint replay
        self._joint_replay = _load_joint_replay()
        if self._joint_replay is None:
            self.get_logger().warn(f"{JOINT_REPLAY_PATH.name} not found, joint topics will not be published")
        else:
            n = len(self._joint_replay["timestamps"])
            dur = self._joint_replay["timestamps"][-1]
            self.get_logger().info(f"Loaded joint replay: {n} samples over {dur:.1f}s")

        # Publishers
        self._slave_pub = self.create_publisher(JointState, "/robot_slave/states", 10)
        self._master_pub = self.create_publisher(JointState, "/robot_master/cmd", 10)
        self._camera_pubs = {topic: self.create_publisher(CompressedImage, topic, 10) for topic in self._camera_frames}

        # Timers
        if self._joint_replay is not None:
            self.create_timer(1.0 / JOINT_HZ, self._publish_joints)
        if self._camera_frames:
            self.create_timer(1.0 / CAMERA_HZ, self._publish_cameras)

        self._fault.log_config()

    def _make_header(self, frame_id: str) -> Header:
        header = Header()
        header.stamp = self.get_clock().now().to_msg()
        header.frame_id = frame_id
        return header

    def _build_joint_msg(self, positions: list[float], *, with_velocity: bool) -> JointState:
        """Build a JointState message."""
        msg = JointState()
        msg.header = self._make_header(JOINT_FRAME_ID)
        msg.name = list(self._joint_replay["joint_names"])  # type: ignore[index]
        msg.position = list(positions)
        # Velocity and effort are not in the recording, so fill with zeros
        # (recorder/analysis only use position)
        msg.velocity = [0.0] * len(positions) if with_velocity else []
        msg.effort = [0.0] * len(positions)
        return msg

    def _joint_index_for_tick(self, tick: int) -> int:
        """100Hz tick → index in joint_replay.timestamps. Loops when elapsed time exceeds the data length."""
        timestamps: list[float] = self._joint_replay["timestamps"]  # type: ignore[index]
        duration = timestamps[-1]
        elapsed = (tick / JOINT_HZ) % duration
        # bisect to get the largest index whose timestamp is <= elapsed
        idx = bisect.bisect_right(timestamps, elapsed) - 1
        return max(0, idx)

    def _publish_joints(self) -> None:
        """Publish master cmd / slave states following the recorded trajectory."""
        burst_state = self._fault.update_burst()
        if burst_state == "gap":
            return

        idx = self._joint_index_for_tick(self._joint_tick)
        master_positions = self._joint_replay["master_positions_rad"][idx]  # type: ignore[index]
        slave_positions = self._joint_replay["slave_positions_rad"][idx]  # type: ignore[index]

        if not self._fault.is_stopped("/robot_slave/states") and not self._fault.should_drop("/robot_slave/states"):
            self._slave_pub.publish(self._build_joint_msg(slave_positions, with_velocity=True))

        if not self._fault.is_stopped("/robot_master/cmd") and not self._fault.should_drop("/robot_master/cmd"):
            self._master_pub.publish(self._build_joint_msg(master_positions, with_velocity=False))

        # During burst: send extra messages to slave all at once
        if burst_state == "burst" and self._fault.burst_remaining > 0:
            n = min(self._fault.burst_remaining, 10)
            for _ in range(n):
                self._slave_pub.publish(self._build_joint_msg(slave_positions, with_velocity=True))
            self._fault.consume_burst(n)

        self._joint_tick += 1

    def _publish_cameras(self) -> None:
        """Loop-publish each camera's corresponding frame sequence."""
        empty_idx_map = {topic: i for i, topic in enumerate(self._camera_frames)}
        for topic, frames in self._camera_frames.items():
            if self._fault.is_stopped(topic):
                continue
            if self._fault.should_drop(topic):
                continue

            jpeg_data = frames[self._camera_frame_idx % len(frames)]
            msg = CompressedImage()
            msg.header = self._make_header(CAMERA_FRAME_ID)
            msg.format = "jpeg"
            msg.data = b"" if self._fault.should_send_empty_frame(empty_idx_map[topic]) else jpeg_data
            self._camera_pubs[topic].publish(msg)

        self._camera_frame_idx += 1


def main() -> None:
    rclpy.init()
    node = RobotSimulator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Simulator shutting down...")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
