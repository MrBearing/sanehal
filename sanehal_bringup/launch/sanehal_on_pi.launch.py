import os
import time

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def _as_bool(value):
    return value.lower() in ('1', 'true', 'yes', 'on')


def _wait_for_dynamixel(context):
    if not _as_bool(LaunchConfiguration('start_control').perform(context)):
        return []
    if _as_bool(LaunchConfiguration('use_mock_hardware').perform(context)):
        return [LogInfo(msg='Mock ros2_control hardware selected; skipping device check.')]
    if not _as_bool(LaunchConfiguration('wait_for_devices').perform(context)):
        return []

    device = LaunchConfiguration('dynamixel_port').perform(context)
    timeout = float(LaunchConfiguration('device_wait_timeout').perform(context))
    deadline = time.monotonic() + timeout
    while time.monotonic() <= deadline:
        if os.path.exists(device) and os.access(device, os.R_OK | os.W_OK):
            return [LogInfo(msg=f'Dynamixel device is ready: {device}')]
        time.sleep(0.1)
    raise RuntimeError(
        f'Dynamixel device {device} did not become readable and writable '
        f'within {timeout:.1f} seconds. Check udev rules and dialout membership.'
    )


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')
    use_mock_hardware = LaunchConfiguration('use_mock_hardware')
    start_description = LaunchConfiguration('start_description')
    start_control = LaunchConfiguration('start_control')
    dynamixel_port = LaunchConfiguration('dynamixel_port')
    dynamixel_baud_rate = LaunchConfiguration('dynamixel_baud_rate')
    controllers_file = LaunchConfiguration('controllers_file')

    arguments = [
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument(
            'use_mock_hardware', default_value='false',
            description='Use ros2_control GenericSystem instead of real Dynamixel hardware.',
        ),
        DeclareLaunchArgument(
            'start_description', default_value='true',
            description='Start robot_state_publisher.',
        ),
        DeclareLaunchArgument(
            'start_control', default_value='true',
            description='Start controller_manager and wheel controllers.',
        ),
        DeclareLaunchArgument(
            'wait_for_devices', default_value='true',
            description='Wait for required hardware devices before starting.',
        ),
        DeclareLaunchArgument(
            'device_wait_timeout', default_value='10.0',
            description='Maximum seconds to wait for a hardware device.',
        ),
        DeclareLaunchArgument(
            'dynamixel_port', default_value='/dev/dxhub',
            description='Dynamixel serial device.',
        ),
        DeclareLaunchArgument(
            'dynamixel_baud_rate', default_value='1000000',
            description='Dynamixel bus baud rate.',
        ),
        DeclareLaunchArgument(
            'controllers_file',
            default_value=PathJoinSubstitution([
                FindPackageShare('sanehal_vehicle_description'),
                'controllers', 'sanehal_controllers.yaml',
            ]),
            description='ros2_control controller parameter file.',
        ),
    ]

    robot_description_content = Command([
        PathJoinSubstitution([FindExecutable(name='xacro')]),
        ' ',
        PathJoinSubstitution([
            FindPackageShare('sanehal_vehicle_description'),
            'urdf', 'sanehal.urdf.xacro',
        ]),
        ' use_mock_hardware:=', use_mock_hardware,
        ' dynamixel_port:=', dynamixel_port,
        ' dynamixel_baud_rate:=', dynamixel_baud_rate,
    ])
    robot_description = {
        'robot_description': ParameterValue(robot_description_content, value_type=str)
    }

    control_node = Node(
        package='controller_manager', executable='ros2_control_node',
        parameters=[robot_description, controllers_file, {'use_sim_time': use_sim_time}],
        output='both', condition=IfCondition(start_control),
    )
    robot_state_publisher = Node(
        package='robot_state_publisher', executable='robot_state_publisher',
        output='both', parameters=[robot_description, {'use_sim_time': use_sim_time}],
        condition=IfCondition(start_description),
    )
    controller_spawner = Node(
        package='controller_manager', executable='spawner', output='screen',
        arguments=[
            'joint_state_broadcaster', 'sanehal_base_controller',
            '--controller-manager', '/controller_manager',
            '--controller-manager-timeout', '30',
            '--service-call-timeout', '10', '--switch-timeout', '10',
            '--activate-as-group',
        ],
        condition=IfCondition(start_control),
    )

    return LaunchDescription(arguments + [
        OpaqueFunction(function=_wait_for_dynamixel),
        control_node, robot_state_publisher, controller_spawner,
    ])
