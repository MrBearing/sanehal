from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    config_file = LaunchConfiguration('config_file')

    config_file_argument = DeclareLaunchArgument(
        'config_file',
        default_value=PathJoinSubstitution(
            [FindPackageShare('sanehal_bringup'), 'config', 'jt16_serial.yaml']
        ),
        description='Full path to the Hesai JT16 driver configuration file.',
    )

    jt16_driver = Node(
        package='hesai_ros_driver',
        executable='hesai_ros_driver_node',
        name='hesai_ros_driver_node',
        output='screen',
        parameters=[{'config_path': config_file}],
    )

    return LaunchDescription([config_file_argument, jt16_driver])
