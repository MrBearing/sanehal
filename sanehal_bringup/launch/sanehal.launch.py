from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    sanehal_bringup = FindPackageShare('sanehal_bringup')

    vehicle = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([sanehal_bringup, '/launch', '/diffbot_on_pi.launch.py'])
    )
    lidar = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([sanehal_bringup, '/launch', '/ld19.launch.py'])
    )

    ld = LaunchDescription()
    ld.add_action(vehicle)
    ld.add_action(lidar)
    return ld
