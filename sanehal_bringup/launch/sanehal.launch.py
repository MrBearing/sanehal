from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    sanehal_bringup = FindPackageShare('sanehal_bringup')
    use_sim_time = LaunchConfiguration('use_sim_time')
    start_lidar = LaunchConfiguration('start_lidar')
    jt16_config_file = LaunchConfiguration('jt16_config_file')

    arguments = [
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use a simulation clock for the robot stack.',
        ),
        DeclareLaunchArgument(
            'start_lidar',
            default_value='true',
            description='Start the Hesai JT16 driver.',
        ),
        DeclareLaunchArgument(
            'jt16_config_file',
            default_value=PathJoinSubstitution(
                [sanehal_bringup, 'config', 'jt16_serial.yaml']
            ),
            description='Full path to the Hesai JT16 driver configuration file.',
        ),
    ]

    vehicle = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [sanehal_bringup, 'launch', 'sanehal_on_pi.launch.py']
            )
        ),
        launch_arguments={'use_sim_time': use_sim_time}.items(),
    )
    lidar = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([sanehal_bringup, 'launch', 'jt16.launch.py'])
        ),
        launch_arguments={'config_file': jt16_config_file}.items(),
        condition=IfCondition(start_lidar),
    )

    return LaunchDescription(arguments + [vehicle, lidar])
