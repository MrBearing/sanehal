from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    bringup_share = FindPackageShare('sanehal_bringup')
    slam_toolbox_share = FindPackageShare('slam_toolbox')

    use_sim_time = LaunchConfiguration('use_sim_time')
    start_robot_bringup = LaunchConfiguration('start_robot_bringup')
    start_rviz = LaunchConfiguration('start_rviz')
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
            'start_rviz',
            default_value='true',
            description='Start RViz with the JT16 SLAM display configuration.',
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

    # Issue #27/#30/#31 own the JT16 driver and PointCloud2-to-LaserScan
    # bringup. This launch consumes their /scan output and deliberately does
    # not start the legacy LD19 path.
    robot_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [bringup_share, 'launch', 'sanehal_on_pi.launch.py']
            )
        ),
        launch_arguments={'use_sim_time': use_sim_time}.items(),
        condition=IfCondition(start_robot_bringup),
    )

    async_slam = IncludeLaunchDescription(
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

    return LaunchDescription(arguments + [robot_bringup, async_slam, rviz])
