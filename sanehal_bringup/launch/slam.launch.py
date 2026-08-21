from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.actions import SetRemap
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    bringup_share = FindPackageShare('sanehal_bringup')
    slam_toolbox_share = FindPackageShare('slam_toolbox')

    use_sim_time = LaunchConfiguration('use_sim_time')
    start_robot_bringup = LaunchConfiguration('start_robot_bringup')
    start_lidar = LaunchConfiguration('start_lidar')
    start_pointcloud_to_laserscan = LaunchConfiguration(
        'start_pointcloud_to_laserscan'
    )
    start_rviz = LaunchConfiguration('start_rviz')
    jt16_config_file = LaunchConfiguration('jt16_config_file')
    converter_params_file = LaunchConfiguration('converter_params_file')
    pointcloud_topic = LaunchConfiguration('pointcloud_topic')
    scan_topic = LaunchConfiguration('scan_topic')
    slam_params_file = LaunchConfiguration('slam_params_file')
    rviz_config_file = LaunchConfiguration('rviz_config_file')

    arguments = [
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use a simulation clock instead of the hardware clock.',
        ),
        DeclareLaunchArgument(
            'start_robot_bringup',
            default_value='true',
            description='Start robot_state_publisher, ros2_control, and wheel odometry.',
        ),
        DeclareLaunchArgument(
            'start_lidar',
            default_value='true',
            description='Start the Hesai JT16 driver.',
        ),
        DeclareLaunchArgument(
            'start_pointcloud_to_laserscan',
            default_value='true',
            description='Convert the JT16 PointCloud2 topic to LaserScan.',
        ),
        DeclareLaunchArgument(
            'start_rviz',
            default_value='true',
            description='Start RViz with the JT16 SLAM display configuration.',
        ),
        DeclareLaunchArgument(
            'jt16_config_file',
            default_value=PathJoinSubstitution(
                [bringup_share, 'config', 'jt16_serial.yaml']
            ),
            description='Full path to the Hesai JT16 driver configuration file.',
        ),
        DeclareLaunchArgument(
            'converter_params_file',
            default_value=PathJoinSubstitution(
                [bringup_share, 'config', 'pointcloud_to_laserscan_jt16.yaml']
            ),
            description='PointCloud2-to-LaserScan parameter file.',
        ),
        DeclareLaunchArgument(
            'pointcloud_topic',
            default_value='/lidar_points',
            description='JT16 PointCloud2 input topic.',
        ),
        DeclareLaunchArgument(
            'scan_topic',
            default_value='/scan',
            description='LaserScan topic consumed by slam_toolbox.',
        ),
        DeclareLaunchArgument(
            'slam_params_file',
            default_value=PathJoinSubstitution(
                [bringup_share, 'config', 'slam_toolbox_jt16.yaml']
            ),
            description='Full path to the slam_toolbox parameter file.',
        ),
        DeclareLaunchArgument(
            'rviz_config_file',
            default_value=PathJoinSubstitution(
                [bringup_share, 'config', 'slam_jt16.rviz']
            ),
            description='Full path to the RViz configuration.',
        ),
    ]

    robot_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [bringup_share, 'launch', 'sanehal_on_pi.launch.py']
            )
        ),
        launch_arguments={'use_sim_time': use_sim_time}.items(),
        condition=IfCondition(start_robot_bringup),
    )

    lidar = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([bringup_share, 'launch', 'jt16.launch.py'])
        ),
        launch_arguments={'config_file': jt16_config_file}.items(),
        condition=IfCondition(start_lidar),
    )

    converter = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [bringup_share, 'launch', 'pointcloud_to_laserscan.launch.py']
            )
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'pointcloud_topic': pointcloud_topic,
            'scan_topic': scan_topic,
            'converter_params_file': converter_params_file,
        }.items(),
        condition=IfCondition(start_pointcloud_to_laserscan),
    )

    async_slam = GroupAction(
        actions=[
            SetRemap(src='/scan', dst=scan_topic),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [slam_toolbox_share, 'launch', 'online_async_launch.py']
                    )
                ),
                launch_arguments={
                    'slam_params_file': slam_params_file,
                    'use_sim_time': use_sim_time,
                    'autostart': 'true',
                }.items(),
            ),
        ]
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_file],
        parameters=[{'use_sim_time': use_sim_time}],
        condition=IfCondition(start_rviz),
    )

    return LaunchDescription(
        arguments + [robot_bringup, lidar, converter, async_slam, rviz]
    )
