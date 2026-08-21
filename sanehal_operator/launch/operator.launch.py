from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')
    fixed_frame = LaunchConfiguration('fixed_frame')
    rviz_config_file = LaunchConfiguration('rviz_config_file')

    arguments = [
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument(
            'fixed_frame', default_value='map',
            description='RViz fixed frame. Use odom when slam_toolbox is disabled.',
        ),
        DeclareLaunchArgument(
            'rviz_config_file',
            default_value=PathJoinSubstitution([
                FindPackageShare('sanehal_operator'),
                'config', 'sanehal2_monitor.rviz',
            ]),
        ),
    ]

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='sanehal_operator_rviz',
        output='screen',
        arguments=['-d', rviz_config_file, '-f', fixed_frame],
        parameters=[{'use_sim_time': use_sim_time}],
    )

    return LaunchDescription(arguments + [rviz])
