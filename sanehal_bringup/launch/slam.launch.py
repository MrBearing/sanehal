"""Compatibility entry point for the integrated Robot-side bringup."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    bringup_share = FindPackageShare('sanehal_bringup')
    names = [
        'use_sim_time', 'start_robot_bringup', 'start_lidar',
        'start_pointcloud_to_laserscan', 'start_rviz', 'jt16_config_file',
        'converter_params_file', 'pointcloud_topic', 'scan_topic',
        'slam_params_file', 'rviz_config_file',
    ]
    cfg = {name: LaunchConfiguration(name) for name in names}
    defaults = {
        'use_sim_time': 'false',
        'start_robot_bringup': 'true',
        'start_lidar': 'true',
        'start_pointcloud_to_laserscan': 'true',
        'start_rviz': 'true',
        'jt16_config_file': PathJoinSubstitution([
            bringup_share, 'config', 'jt16_serial.yaml',
        ]),
        'converter_params_file': PathJoinSubstitution([
            bringup_share, 'config', 'pointcloud_to_laserscan_jt16.yaml',
        ]),
        'pointcloud_topic': '/lidar_points',
        'scan_topic': '/scan',
        'slam_params_file': PathJoinSubstitution([
            bringup_share, 'config', 'slam_toolbox_jt16.yaml',
        ]),
        'rviz_config_file': PathJoinSubstitution([
            bringup_share, 'config', 'slam_jt16.rviz',
        ]),
    }
    arguments = [
        DeclareLaunchArgument(name, default_value=defaults[name]) for name in names
    ]

    integrated_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([
            bringup_share, 'launch', 'sanehal.launch.py',
        ])),
        launch_arguments={
            'use_sim_time': cfg['use_sim_time'],
            'start_description': cfg['start_robot_bringup'],
            'start_control': cfg['start_robot_bringup'],
            'start_lidar': cfg['start_lidar'],
            'start_pointcloud_to_laserscan': cfg['start_pointcloud_to_laserscan'],
            'start_slam': 'true',
            'start_rviz': cfg['start_rviz'],
            'jt16_config_file': cfg['jt16_config_file'],
            'converter_params_file': cfg['converter_params_file'],
            'pointcloud_topic': cfg['pointcloud_topic'],
            'scan_topic': cfg['scan_topic'],
            'slam_params_file': cfg['slam_params_file'],
            'rviz_config_file': cfg['rviz_config_file'],
        }.items(),
    )
    return LaunchDescription(arguments + [integrated_bringup])
