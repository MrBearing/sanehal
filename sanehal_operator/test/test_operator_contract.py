from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def test_operator_launch_is_display_only():
    launch_text = (PACKAGE_ROOT / 'launch' / 'operator.launch.py').read_text()
    assert "package='rviz2'" in launch_text
    for forbidden in ('controller_manager', 'robot_state_publisher', 'hesai_ros_driver'):
        assert forbidden not in launch_text


def test_rviz_monitoring_contract():
    config = (PACKAGE_ROOT / 'config' / 'sanehal2_monitor.rviz').read_text()
    for topic in (
        '/map', '/scan', '/sanehal_base_controller/odom', '/pose',
        '/lidar_points', '/robot_description',
    ):
        assert f'Value: {topic}' in config
    pointcloud = config.split('Name: JT16 PointCloud2 (debug only)', 1)[1]
    pointcloud = pointcloud.split('Class: rviz_default_plugins/TF', 1)[0]
    assert 'Value: false' in pointcloud
    assert 'Fixed Frame: map' in config
