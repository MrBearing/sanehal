#!/usr/bin/env python3

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # Declare launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    slam_params_file = LaunchConfiguration('slam_params_file')

    declare_use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation/Gazebo clock'
    )
    
    declare_slam_params_file_arg = DeclareLaunchArgument(
        'slam_params_file',
        default_value=PathJoinSubstitution([
            FindPackageShare('sanehal_bringup'),
            'config',
            'slam_toolbox_params.yaml'
        ]),
        description='Full path to the SLAM Toolbox parameters file'
    )

    # Include the robot launch file
    robot_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('sanehal_bringup'),
                'launch',
                'sanehal.launch.py'
            ])
        ]),
        launch_arguments={
            'use_sim_time': use_sim_time,
        }.items()
    )

    # SLAM Toolbox node
    slam_toolbox_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[
            slam_params_file,
            {'use_sim_time': use_sim_time}
        ],
        remappings=[
            ('/scan', '/scan'),
        ]
    )

    # RViz2 for visualization
    rviz2_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', PathJoinSubstitution([
            FindPackageShare('sanehal_bringup'),
            'rviz',
            'slam.rviz'
        ])],
        parameters=[{'use_sim_time': use_sim_time}]
    )

    return LaunchDescription([
        declare_use_sim_time_arg,
        declare_slam_params_file_arg,
        robot_launch,
        slam_toolbox_node,
        rviz2_node,
    ])