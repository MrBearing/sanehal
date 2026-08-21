"""Compatibility entry point for the integrated Robot-side bringup."""

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    integrated_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([
            FindPackageShare('sanehal_bringup'), 'launch', 'sanehal.launch.py',
        ])),
        launch_arguments={'start_slam': 'true'}.items(),
    )
    return LaunchDescription([integrated_bringup])
