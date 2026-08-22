from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = PACKAGE_ROOT.parent


def test_operator_launch_is_display_only():
    launch_text = (PACKAGE_ROOT / 'launch' / 'operator.launch.py').read_text()
    assert "package='rviz2'" in launch_text
    for forbidden in ('controller_manager', 'robot_state_publisher', 'hesai_ros_driver'):
        assert forbidden not in launch_text


def test_operator_launch_has_opt_in_playstation_teleop():
    launch_text = (PACKAGE_ROOT / 'launch' / 'operator.launch.py').read_text()
    assert "'enable_teleop', default_value='false'" in launch_text
    assert "choices=['DualShock3', 'DualShock4', 'DualSense']" in launch_text
    assert "package='joy'" in launch_text
    assert "executable='gamepad_teleop_node'" in launch_text
    assert "default_value='/sanehal_base_controller/cmd_vel'" in launch_text


def test_gamepad_safety_defaults():
    config = (PACKAGE_ROOT / 'config' / 'gamepad_teleop.yaml').read_text()
    for setting in (
        'sticky_buttons: false', 'autorepeat_rate: 20.0',
        'deadman_button: L1', 'turbo_button: R1',
        'linear_speed: 0.05', 'angular_speed: 0.30',
        'turbo_linear_speed: 0.10', 'turbo_angular_speed: 0.60',
        'joy_timeout: 0.25',
        'cmd_vel_topic: /sanehal_base_controller/cmd_vel',
    ):
        assert setting in config


def test_teleop_publishes_stamped_commands_and_has_watchdog():
    source = (PACKAGE_ROOT / 'src' / 'gamepad_teleop_node.cpp').read_text()
    header = (
        PACKAGE_ROOT / 'include' / 'sanehal_operator' /
        'gamepad_teleop_node.hpp'
    ).read_text()
    assert 'geometry_msgs/msg/twist_stamped.hpp' in header
    assert 'p9n_interface::PlayStationInterface' in header
    assert 'std::chrono::steady_clock' in header
    assert 'button_pressed(deadman_button_)' in source
    assert 'Joy input timed out; commanding stop' in source
    assert 'std::isfinite(timeout)' in source
    assert 'std::isfinite(turbo_angular_speed_)' in source
    publisher_position = source.index('command_publisher_ = create_publisher')
    stop_position = source.index('publish_stop();', publisher_position)
    subscription_position = source.index('joy_subscription_ =', publisher_position)
    assert publisher_position < stop_position < subscription_position

    cmake = (PACKAGE_ROOT / 'CMakeLists.txt').read_text()
    assert 'target_compile_features(gamepad_teleop_node PUBLIC cxx_std_17)' in cmake


def test_playstation_dependency_is_pinned_consistently():
    revision = '75a79bbe1af6012a3ab1a77f3d380cf1fd8c3d17'
    workspace_repos = (REPOSITORY_ROOT / 'build_depends.repos').read_text()
    image_repos = (
        REPOSITORY_ROOT / 'docker' / 'operator' /
        'operator_depends.repos'
    ).read_text()
    assert revision in workspace_repos
    assert revision in image_repos
    assert 'PlayStation-JoyInterface-ROS2' in workspace_repos


def test_gamepad_compose_exposes_only_selected_device():
    compose = (REPOSITORY_ROOT / 'compose.operator.gamepad.yaml').read_text()
    assert '${GAMEPAD_DEVICE:?GAMEPAD_DEVICE is required}' in compose
    assert '${INPUT_GID:?INPUT_GID is required}' in compose
    assert 'privileged:' not in compose
    assert '/dev/input:/dev/input' not in compose


def test_startup_revalidates_stable_gamepad_link():
    script = (REPOSITORY_ROOT / 'scripts' / 'operator' / 'up.sh').read_text()
    assert 'current_gamepad_device=$(readlink -f "${gamepad_by_id}")' in script
    assert '"${current_gamepad_device}" != "${gamepad_device}"' in script
    assert '[ -z "${gamepad_by_id}" ]' in script
    assert 'GAMEPAD_BY_ID is missing.' in script


def test_configuration_checks_container_group_read_permission():
    script = (
        REPOSITORY_ROOT / 'scripts' / 'operator' / 'configure.sh'
    ).read_text()
    assert "device_permissions=$(stat -c '%A'" in script
    assert '"${device_permissions:4:1}" != "r"' in script
    assert '[ ! -r "${gamepad_device}" ]' not in script


def test_rviz_monitoring_contract():
    config = (PACKAGE_ROOT / 'config' / 'sanehal2_monitor.rviz').read_text()
    for topic in (
        '/map', '/scan', '/sanehal_base_controller/odom', '/pose',
        '/lidar_points', '/robot_description',
    ):
        assert f'Value: {topic}' in config
    pointcloud = config.split('Name: JT16 PointCloud2 (debug only)', 1)[1]
    pointcloud = pointcloud.split('Class: rviz_default_plugins/TF', 1)[0]
    assert 'Value: false' in pointcloud
    assert 'Fixed Frame: map' in config
