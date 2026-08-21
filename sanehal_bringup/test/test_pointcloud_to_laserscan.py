import math
import time
import unittest

from ament_index_python.packages import get_package_share_directory
import launch
import launch_ros.actions
import launch_testing.actions
import pytest
import rclpy
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan, PointCloud2, PointField
from sensor_msgs_py import point_cloud2


@pytest.mark.launch_test
def generate_test_description():
    params_file = (
        get_package_share_directory('sanehal_bringup')
        + '/config/pointcloud_to_laserscan_jt16.yaml'
    )
    converter = launch_ros.actions.Node(
        package='pointcloud_to_laserscan',
        executable='pointcloud_to_laserscan_node',
        name='pointcloud_to_laserscan',
        parameters=[params_file],
        remappings=[
            ('cloud_in', '/test/lidar_points'),
            ('scan', '/test/scan'),
        ],
    )

    return (
        launch.LaunchDescription(
            [converter, launch_testing.actions.ReadyToTest()]
        ),
        {'converter': converter},
    )


class TestPointCloudToLaserScan(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rclpy.init()

    @classmethod
    def tearDownClass(cls):
        rclpy.shutdown()

    def setUp(self):
        self.node = rclpy.create_node('test_pointcloud_to_laserscan')
        self.scan = None
        self.scan_subscription = self.node.create_subscription(
            LaserScan,
            '/test/scan',
            self._scan_callback,
            qos_profile_sensor_data,
        )
        self.cloud_publisher = self.node.create_publisher(
            PointCloud2,
            '/test/lidar_points',
            qos_profile_sensor_data,
        )

    def tearDown(self):
        self.node.destroy_node()

    def _scan_callback(self, msg):
        self.scan = msg

    def _make_cloud(self):
        fields = [
            PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1),
        ]
        from std_msgs.msg import Header
        cloud_header = Header(
            stamp=self.node.get_clock().now().to_msg(),
            frame_id='hesai_lidar',
        )
        points = [
            (1.0, 0.0, 0.0),
            (2.0, 0.0, 0.0),
            (1.0, 1.0, 0.20),
            (0.1, 0.0, 0.0),
            (math.nan, 0.0, 0.0),
        ]
        return point_cloud2.create_cloud(cloud_header, fields, points)

    def test_projection_contract(self):
        cloud = self._make_cloud()
        deadline = time.monotonic() + 10.0
        while self.scan is None and time.monotonic() < deadline:
            self.cloud_publisher.publish(cloud)
            rclpy.spin_once(self.node, timeout_sec=0.1)

        self.assertIsNotNone(self.scan)
        scan = self.scan
        self.assertEqual(scan.header.frame_id, 'hesai_lidar')
        self.assertEqual(scan.header.stamp, cloud.header.stamp)
        self.assertAlmostEqual(scan.angle_min, -3.14159265, places=6)
        self.assertAlmostEqual(scan.angle_max, 3.14159264, places=6)
        self.assertAlmostEqual(scan.angle_increment, 0.010471976, places=7)
        self.assertAlmostEqual(scan.scan_time, 0.2, places=6)
        self.assertAlmostEqual(scan.range_min, 0.3, places=6)
        self.assertAlmostEqual(scan.range_max, 30.0, places=6)
        self.assertEqual(len(scan.ranges), 600)
        self.assertEqual(len(scan.intensities), 0)

        zero_angle_index = int((0.0 - scan.angle_min) / scan.angle_increment)
        self.assertAlmostEqual(scan.ranges[zero_angle_index], 1.0, places=6)
        finite_ranges = [value for value in scan.ranges if math.isfinite(value)]
        self.assertEqual(finite_ranges, [1.0])
        self.assertTrue(math.isinf(scan.ranges[0]))
