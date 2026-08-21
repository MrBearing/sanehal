from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    bringup_share = FindPackageShare('sanehal_bringup')

    use_sim_time = LaunchConfiguration('use_sim_time')
    pointcloud_topic = LaunchConfiguration('pointcloud_topic')
    scan_topic = LaunchConfiguration('scan_topic')
    converter_params_file = LaunchConfiguration('converter_params_file')

    arguments = [
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use a simulation clock instead of the hardware clock.',
        ),
        DeclareLaunchArgument(
            'pointcloud_topic',
            default_value='/lidar_points',
            description='JT16 PointCloud2 input topic.',
        ),
        DeclareLaunchArgument(
            'scan_topic',
            default_value='/scan',
            description='LaserScan output topic.',
        ),
        DeclareLaunchArgument(
            'converter_params_file',
            default_value=PathJoinSubstitution(
                [bringup_share, 'config', 'pointcloud_to_laserscan_jt16.yaml']
            ),
            description='PointCloud2-to-LaserScan parameter file.',
        ),
    ]

    converter = Node(
        package='pointcloud_to_laserscan',
        executable='pointcloud_to_laserscan_node',
        name='pointcloud_to_laserscan',
        output='screen',
        parameters=[converter_params_file, {'use_sim_time': use_sim_time}],
        remappings=[
            ('cloud_in', pointcloud_topic),
            ('scan', scan_topic),
        ],
    )

    return LaunchDescription(arguments + [converter])
