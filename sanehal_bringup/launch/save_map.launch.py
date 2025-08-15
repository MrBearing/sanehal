#!/usr/bin/env python3

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node


def generate_launch_description():
    # Declare launch arguments
    map_name = LaunchConfiguration('map_name', default='my_map')
    
    declare_map_name_arg = DeclareLaunchArgument(
        'map_name',
        default_value='my_map',
        description='Name of the map to save (without extension)'
    )

    # Save map using nav2_map_server
    save_map_cmd = ExecuteProcess(
        cmd=['ros2', 'run', 'nav2_map_server', 'map_saver_cli',
             '-f', map_name],
        output='screen'
    )

    return LaunchDescription([
        declare_map_name_arg,
        save_map_cmd,
    ])