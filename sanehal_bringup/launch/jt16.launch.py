import os
import time

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo, OpaqueFunction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    config_file = LaunchConfiguration('config_file')
    use_sim_time = LaunchConfiguration('use_sim_time')

    def wait_for_devices(context):
        if LaunchConfiguration('wait_for_devices').perform(context).lower() not in (
            '1', 'true', 'yes', 'on'
        ):
            return []
        devices = [
            LaunchConfiguration('rs485_device').perform(context),
            LaunchConfiguration('rs232_device').perform(context),
        ]
        timeout = float(LaunchConfiguration('device_wait_timeout').perform(context))
        deadline = time.monotonic() + timeout
        while time.monotonic() <= deadline:
            missing = [
                path for path in devices
                if not (os.path.exists(path) and os.access(path, os.R_OK | os.W_OK))
            ]
            if not missing:
                return [LogInfo(msg=f'JT16 serial devices are ready: {devices}')]
            time.sleep(0.1)
        raise RuntimeError(
            f'JT16 devices not readable and writable after {timeout:.1f}s: {missing}. '
            'Check the config file, udev rules, and dialout membership.'
        )

    config_file_argument = DeclareLaunchArgument(
        'config_file',
        default_value=PathJoinSubstitution(
            [FindPackageShare('sanehal_bringup'), 'config', 'jt16_serial.yaml']
        ),
        description='Full path to the Hesai JT16 driver configuration file.',
    )
    arguments = [
        config_file_argument,
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument('wait_for_devices', default_value='true'),
        DeclareLaunchArgument('device_wait_timeout', default_value='10.0'),
        DeclareLaunchArgument('rs485_device', default_value='/dev/jt16_rs485'),
        DeclareLaunchArgument('rs232_device', default_value='/dev/jt16_rs232'),
    ]

    jt16_driver = Node(
        package='hesai_ros_driver',
        executable='hesai_ros_driver_node',
        name='hesai_ros_driver_node',
        output='screen',
        parameters=[{'config_path': config_file, 'use_sim_time': use_sim_time}],
    )

    return LaunchDescription(
        arguments + [OpaqueFunction(function=wait_for_devices), jt16_driver]
    )
