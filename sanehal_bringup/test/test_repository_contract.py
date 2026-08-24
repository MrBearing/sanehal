from pathlib import Path
import re

import yaml


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_source_dependencies_are_pinned():
    repos = yaml.safe_load(
        (REPOSITORY_ROOT / 'build_depends.repos').read_text(encoding='utf-8')
    )['repositories']
    commit = re.compile(r'^[0-9a-f]{40}$')
    for name in (
        'PlayStation-JoyInterface-ROS2',
        'DynamixelSDK',
        'dynamixel_hardware_interface',
        'dynamixel_interfaces',
    ):
        assert commit.fullmatch(repos[name]['version']), name
    assert repos['HesaiLidar_ROS_2.0']['version'] == 'v2.0.12'


def test_setup_does_not_update_existing_source_repositories():
    setup = (REPOSITORY_ROOT / 'setup.bash').read_text(encoding='utf-8')
    assert '--skip-existing' in setup
    assert 'vcs pull' not in setup
    assert 'ROS_DISTRO:-' in setup
    assert '--rosdistro jazzy' in setup
    assert 'for command_name in vcs rosdep; do' in setup


def test_wheel_cylinder_axial_inertia_stays_on_local_z():
    xacro = (
        REPOSITORY_ROOT / 'sanehal_vehicle_description/urdf/sanehal.xacro'
    ).read_text(encoding='utf-8')
    axial_izz = (
        'izz="${wheel_mass / 2.0 * wheel_radius*wheel_radius}"'
    )
    assert xacro.count(axial_izz) == 2


def test_removed_runtime_dependencies_do_not_return():
    package = (REPOSITORY_ROOT / 'sanehal/package.xml').read_text(encoding='utf-8')
    vehicle_package = (
        REPOSITORY_ROOT / 'sanehal_vehicle_description/package.xml'
    ).read_text(encoding='utf-8')
    dependency_manifest = (
        REPOSITORY_ROOT / 'build_depends.repos'
    ).read_text(encoding='utf-8')
    assert 'sanehal_vehicle_sandbox' not in package
    assert '<exec_depend>mock_components</exec_depend>' not in vehicle_package
    assert 'ldlidar' not in dependency_manifest.lower()
    assert 'ld19' not in dependency_manifest.lower()


def test_issue_29_runbook_keeps_safety_and_evidence_gates():
    runbook = (
        REPOSITORY_ROOT / 'docs/sanehal2_system_integration.md'
    ).read_text(encoding='utf-8')
    for required in (
        'Readiness gate',
        'Teleoperation safety sequence',
        'Mapping, recovery, and shutdown',
        'Acceptance cases',
        'Evidence record',
        'F01',
        'E01',
        'X01',
        'Issue #47',
    ):
        assert required in runbook
