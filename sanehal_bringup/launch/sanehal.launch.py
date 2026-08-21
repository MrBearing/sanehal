from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node, SetRemap
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    bringup_share = FindPackageShare('sanehal_bringup')
    description_share = FindPackageShare('sanehal_vehicle_description')
    slam_toolbox_share = FindPackageShare('slam_toolbox')

    names = [
        'use_sim_time', 'use_mock_hardware', 'start_description', 'start_control',
        'start_lidar', 'start_pointcloud_to_laserscan', 'start_slam', 'start_rviz',
        'wait_for_devices', 'device_wait_timeout', 'dynamixel_port',
        'dynamixel_baud_rate', 'controllers_file', 'jt16_config_file',
        'converter_params_file', 'slam_params_file', 'rviz_config_file',
        'pointcloud_topic', 'scan_topic', 'jt16_rs485_device', 'jt16_rs232_device',
        'require_jt16_rs232',
    ]
    cfg = {name: LaunchConfiguration(name) for name in names}

    arguments = [
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument('use_mock_hardware', default_value='false'),
        DeclareLaunchArgument('start_description', default_value='true'),
        DeclareLaunchArgument('start_control', default_value='true'),
        DeclareLaunchArgument('start_lidar', default_value='true'),
        DeclareLaunchArgument('start_pointcloud_to_laserscan', default_value='true'),
        DeclareLaunchArgument('start_slam', default_value='true'),
        DeclareLaunchArgument(
            'start_rviz', default_value='false',
            description='Start RViz locally. Keep false on the Raspberry Pi.',
        ),
        DeclareLaunchArgument('wait_for_devices', default_value='true'),
        DeclareLaunchArgument('device_wait_timeout', default_value='10.0'),
        DeclareLaunchArgument('dynamixel_port', default_value='/dev/dxhub'),
        DeclareLaunchArgument('dynamixel_baud_rate', default_value='1000000'),
        DeclareLaunchArgument(
            'controllers_file',
            default_value=PathJoinSubstitution([
                description_share, 'controllers', 'sanehal_controllers.yaml',
            ]),
        ),
        DeclareLaunchArgument(
            'jt16_config_file',
            default_value=PathJoinSubstitution([
                bringup_share, 'config', 'jt16_serial.yaml',
            ]),
        ),
        DeclareLaunchArgument(
            'converter_params_file',
            default_value=PathJoinSubstitution([
                bringup_share, 'config', 'pointcloud_to_laserscan_jt16.yaml',
            ]),
        ),
        DeclareLaunchArgument(
            'slam_params_file',
            default_value=PathJoinSubstitution([
                bringup_share, 'config', 'slam_toolbox_jt16.yaml',
            ]),
        ),
        DeclareLaunchArgument(
            'rviz_config_file',
            default_value=PathJoinSubstitution([
                bringup_share, 'config', 'slam_jt16.rviz',
            ]),
        ),
        DeclareLaunchArgument('pointcloud_topic', default_value='/lidar_points'),
        DeclareLaunchArgument('scan_topic', default_value='/scan'),
        DeclareLaunchArgument('jt16_rs485_device', default_value='/dev/jt16_rs485'),
        DeclareLaunchArgument('jt16_rs232_device', default_value='/dev/jt16_rs232'),
        DeclareLaunchArgument(
            'require_jt16_rs232', default_value='true',
            description=(
                'Require the JT16 RS232 port during preflight. Set false only '
                'when jt16_config_file supplies a correction_file_path.'
            ),
        ),
    ]

    vehicle = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([
            bringup_share, 'launch', 'sanehal_on_pi.launch.py',
        ])),
        launch_arguments={
            'use_sim_time': cfg['use_sim_time'],
            'use_mock_hardware': cfg['use_mock_hardware'],
            'start_description': cfg['start_description'],
            'start_control': cfg['start_control'],
            'wait_for_devices': cfg['wait_for_devices'],
            'device_wait_timeout': cfg['device_wait_timeout'],
            'dynamixel_port': cfg['dynamixel_port'],
            'dynamixel_baud_rate': cfg['dynamixel_baud_rate'],
            'controllers_file': cfg['controllers_file'],
        }.items(),
    )

    lidar = GroupAction(
        actions=[
            SetRemap(src='/lidar_points', dst=cfg['pointcloud_topic']),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(PathJoinSubstitution([
                    bringup_share, 'launch', 'jt16.launch.py',
                ])),
                launch_arguments={
                    'config_file': cfg['jt16_config_file'],
                    'use_sim_time': cfg['use_sim_time'],
                    'wait_for_devices': cfg['wait_for_devices'],
                    'device_wait_timeout': cfg['device_wait_timeout'],
                    'rs485_device': cfg['jt16_rs485_device'],
                    'rs232_device': cfg['jt16_rs232_device'],
                    'require_rs232': cfg['require_jt16_rs232'],
                }.items(),
            ),
        ],
        condition=IfCondition(cfg['start_lidar']),
    )

    converter = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([
            bringup_share, 'launch', 'pointcloud_to_laserscan.launch.py',
        ])),
        launch_arguments={
            'use_sim_time': cfg['use_sim_time'],
            'pointcloud_topic': cfg['pointcloud_topic'],
            'scan_topic': cfg['scan_topic'],
            'converter_params_file': cfg['converter_params_file'],
        }.items(),
        condition=IfCondition(cfg['start_pointcloud_to_laserscan']),
    )

    slam = GroupAction(
        actions=[
            SetRemap(src='/scan', dst=cfg['scan_topic']),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(PathJoinSubstitution([
                    slam_toolbox_share, 'launch', 'online_async_launch.py',
                ])),
                launch_arguments={
                    'slam_params_file': cfg['slam_params_file'],
                    'use_sim_time': cfg['use_sim_time'],
                    'autostart': 'true',
                }.items(),
            ),
        ],
        condition=IfCondition(cfg['start_slam']),
    )

    rviz = Node(
        package='rviz2', executable='rviz2', name='rviz2', output='screen',
        arguments=['-d', cfg['rviz_config_file']],
        parameters=[{'use_sim_time': cfg['use_sim_time']}],
        remappings=[
            ('/lidar_points', cfg['pointcloud_topic']),
            ('/scan', cfg['scan_topic']),
        ],
        condition=IfCondition(cfg['start_rviz']),
    )

    return LaunchDescription(arguments + [vehicle, lidar, converter, slam, rviz])
