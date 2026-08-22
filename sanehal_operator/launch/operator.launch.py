from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')
    fixed_frame = LaunchConfiguration('fixed_frame')
    rviz_config_file = LaunchConfiguration('rviz_config_file')
    enable_teleop = LaunchConfiguration('enable_teleop')
    gamepad_model = LaunchConfiguration('gamepad_model')
    gamepad_config_file = LaunchConfiguration('gamepad_config_file')
    cmd_vel_topic = LaunchConfiguration('cmd_vel_topic')

    arguments = [
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument(
            'enable_teleop', default_value='false',
            description='Start USB PlayStation joy and safe teleop nodes.',
        ),
        DeclareLaunchArgument(
            'gamepad_model', default_value='DualSense',
            choices=['DualShock3', 'DualShock4', 'DualSense'],
        ),
        DeclareLaunchArgument(
            'cmd_vel_topic', default_value='/sanehal_base_controller/cmd_vel',
            description='TwistStamped Robot controller command topic.',
        ),
        DeclareLaunchArgument(
            'gamepad_config_file',
            default_value=PathJoinSubstitution([
                FindPackageShare('sanehal_operator'),
                'config', 'gamepad_teleop.yaml',
            ]),
        ),
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

    joy = Node(
        package='joy',
        executable='joy_node',
        namespace='operator',
        name='joy',
        output='screen',
        parameters=[gamepad_config_file],
        condition=IfCondition(enable_teleop),
    )
    teleop = Node(
        package='sanehal_operator',
        executable='gamepad_teleop_node',
        namespace='operator',
        name='gamepad_teleop',
        output='screen',
        parameters=[
            gamepad_config_file,
            {'hw_type': gamepad_model, 'cmd_vel_topic': cmd_vel_topic},
        ],
        condition=IfCondition(enable_teleop),
    )

    return LaunchDescription(arguments + [rviz, joy, teleop])
