from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')
    fixed_frame = LaunchConfiguration('fixed_frame')

    use_sim_time_argument = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use a simulation clock in RViz.',
    )
    fixed_frame_argument = DeclareLaunchArgument(
        'fixed_frame',
        default_value='odom',
        description='RViz fixed frame; use map when slam_toolbox is running.',
    )

    rviz_config_file = PathJoinSubstitution(
        [FindPackageShare('sanehal_bringup'), 'config', 'slam_jt16.rviz']
    )
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_file, '-f', fixed_frame],
        parameters=[{'use_sim_time': use_sim_time}],
    )

    return LaunchDescription([use_sim_time_argument, fixed_frame_argument, rviz])
