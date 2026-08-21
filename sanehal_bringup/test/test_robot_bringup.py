import time
import unittest

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
import launch_testing.actions
from nav_msgs.msg import Odometry
import pytest
import rclpy
from sensor_msgs.msg import JointState
from tf2_ros import Buffer, TransformListener


@pytest.mark.launch_test
def generate_test_description():
    launch_file = (
        get_package_share_directory('sanehal_bringup')
        + '/launch/sanehal.launch.py'
    )
    bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(launch_file),
        launch_arguments={
            'use_mock_hardware': 'true',
            'wait_for_devices': 'false',
            'start_lidar': 'false',
            'start_pointcloud_to_laserscan': 'false',
            'start_slam': 'false',
            'start_rviz': 'false',
        }.items(),
    )
    return LaunchDescription([bringup, launch_testing.actions.ReadyToTest()])


class TestRobotBringup(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rclpy.init()

    @classmethod
    def tearDownClass(cls):
        rclpy.shutdown()

    def setUp(self):
        self.node = rclpy.create_node('test_robot_bringup')
        self.joint_state = None
        self.odom = None
        self.node.create_subscription(
            JointState, '/joint_states', self._on_joint_state, 10
        )
        self.node.create_subscription(
            Odometry, '/sanehal_base_controller/odom', self._on_odom, 10
        )
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self.node)

    def tearDown(self):
        self.node.destroy_node()

    def _on_joint_state(self, message):
        self.joint_state = message

    def _on_odom(self, message):
        self.odom = message

    def test_controller_topics_and_tf_contract(self):
        deadline = time.monotonic() + 20.0
        transforms_ready = False
        while time.monotonic() < deadline:
            rclpy.spin_once(self.node, timeout_sec=0.1)
            transforms_ready = (
                self.tf_buffer.can_transform('odom', 'base_footprint', rclpy.time.Time())
                and self.tf_buffer.can_transform(
                    'base_footprint', 'base_link', rclpy.time.Time()
                )
                and self.tf_buffer.can_transform(
                    'base_footprint', 'hesai_lidar', rclpy.time.Time()
                )
            )
            if self.joint_state is not None and self.odom is not None and transforms_ready:
                break

        self.assertIsNotNone(self.joint_state)
        self.assertEqual(
            set(self.joint_state.name),
            {'left_wheel_joint', 'right_wheel_joint'},
        )
        self.assertIsNotNone(self.odom)
        self.assertEqual(self.odom.header.frame_id, 'odom')
        self.assertEqual(self.odom.child_frame_id, 'base_footprint')
        self.assertTrue(transforms_ready)
