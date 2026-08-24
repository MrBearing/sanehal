# SANEHAL-2 system integration and operations

This runbook is the acceptance procedure for GitHub Issue #29. Record the exact
repository commit, dependency revisions, host versions, operators, start/end
times, and every result. Do not drive when a readiness or raised-wheel safety
case has failed.

## Execution ownership

- Raspberry Pi 5 (`sanehal-pi5`): Dynamixel hardware, robot description, JT16,
  PointCloud2-to-LaserScan, and `slam_toolbox`.
- Operator PC: Docker/Jazzy clean build, DDS discovery, RViz, USB gamepad, Wi-Fi
  interruption, and evidence collection.
- Robot-side observer: clear the course and retain immediate access to the
  physical power or emergency-stop control.

Do not coordinate a Wi-Fi-loss test only through an SSH session on the Wi-Fi
link being interrupted. Start Robot-side logging first and retain a local
console or an independent management path.

## Readiness gate

- [ ] Branch and commit recorded; working-tree changes unrelated to #29 excluded.
- [ ] Robot is Ubuntu 24.04 / ROS 2 Jazzy on Raspberry Pi 5 with adequate power.
- [ ] Operator uses the repository's Ubuntu 24.04 / Jazzy container.
- [ ] `/dev/dxhub`, `/dev/jt16_rs485`, and `/dev/jt16_rs232` exist and are RW.
- [ ] Dynamixel IDs are left=2/right=1 at 1 Mbps; wheels initially raised.
- [ ] Robot and Operator use the same unique `ROS_DOMAIN_ID`,
  `rmw_fastrtps_cpp`, `SUBNET` discovery, and `ROS_LOCALHOST_ONLY=0`.
- [ ] The AP permits client-to-client multicast; firewall policy is recorded.
- [ ] `timedatectl status` shows both clocks synchronized; observed skew recorded.
- [ ] A stable `/dev/input/by-id/*-event-joystick` device and model are recorded.
- [ ] L1 deadman, R1 turbo, axes, USB data cable, and single `cmd_vel` publisher
  are confirmed before motor power is enabled.
- [ ] Course, exclusion zone, battery, cables, observer, and physical stop are ready.

## Clean environment

Use a new Noble/Jazzy container or empty Docker build/install/log volumes. The
Operator host distribution is not a substitute for this check.

```bash
source /opt/ros/jazzy/setup.bash
sudo apt-get update
sudo apt-get install -y libboost-all-dev libyaml-cpp-dev python3-rosdep python3-vcstool
mkdir -p /tmp/sanehal_ws/src
cd /tmp/sanehal_ws/src
git clone --branch feature/issue-29-system-integration \
  https://github.com/MrBearing/sanehal.git
cd sanehal
./setup.bash
cd /tmp/sanehal_ws
colcon build --symlink-install
source install/setup.bash
colcon test
colcon test-result --verbose
```

For a pre-push local run, mount the current checkout instead of cloning an
unpublished branch. Never reuse source dependency checkouts from a different
test without comparing `vcs export --exact src` with `build_depends.repos`.

## Robot startup and preflight

Install udev rules and re-login after changing `dialout` membership. With the
wheels raised, start drive/TF without the sensor stack first:

```bash
source /opt/ros/jazzy/setup.bash
source ~/ws_sanehal/install/setup.bash
ls -l /dev/dxhub /dev/jt16_rs485 /dev/jt16_rs232
ros2 launch sanehal_bringup sanehal.launch.py \
  start_lidar:=false start_pointcloud_to_laserscan:=false start_slam:=false
```

From a second Robot console:

```bash
ros2 control list_hardware_components
ros2 control list_hardware_interfaces
ros2 control list_controllers
ros2 topic hz /joint_states
ros2 topic hz /sanehal_base_controller/odom
ros2 run tf2_ros tf2_echo odom base_footprint
```

Only the official ROBOTIS `dynamixel_hardware_interface` is permitted in the
production run. `use_mock_hardware:=true` is limited to automated tests.

After the raised-wheel direction and timeout cases pass, stop the drive-only
launch and start the complete Robot stack:

```bash
ros2 launch sanehal_bringup sanehal.launch.py 2>&1 | \
  tee issue29-robot-$(date -u +%Y%m%dT%H%M%SZ).log
```

Validate its contracts:

```bash
ros2 lifecycle get /slam_toolbox
ros2 topic info /lidar_points --verbose
ros2 topic hz /lidar_points
ros2 topic bw /lidar_points
ros2 topic echo /lidar_points --once --field header
ros2 topic echo /lidar_packets_loss
ros2 topic info /scan --verbose
ros2 topic hz /scan
ros2 topic echo /scan --once
ros2 topic hz /sanehal_base_controller/odom
ros2 run tf2_ros tf2_echo map odom
ros2 run tf2_ros tf2_echo odom base_footprint
ros2 run tf2_ros tf2_echo base_link hesai_lidar
ros2 topic echo /map --once
```

The SANEHAL-2 serial stream acceptance baseline is approximately 5 Hz for both
`/lidar_points` and `/scan`. The JT16 driver configuration's 10 Hz value is a
device nominal, not the measured serial acceptance rate. PointCloud2 must have
nonzero points and fields `x`, `y`, `z`, `intensity`, `ring`, and `timestamp`.

## Operator startup

On the Operator host, configure the stable gamepad device and matching domain:

```bash
ROS_DOMAIN_ID=<domain> \
GAMEPAD_BY_ID=/dev/input/by-id/<controller>-event-joystick \
GAMEPAD_MODEL=<DualShock3|DualShock4|DualSense> \
scripts/operator/configure.sh
scripts/operator/up.sh
```

Inside the Operator container run:

```bash
ros2 daemon stop
ros2 node list
ros2 topic list -t
ros2 lifecycle get /slam_toolbox
ros2 topic info /map --verbose
ros2 topic info /scan --verbose
ros2 topic info /sanehal_base_controller/odom --verbose
ros2 topic info /sanehal_base_controller/cmd_vel --verbose
ros2 topic hz /scan
ros2 topic bw /scan
```

RViz must show `/map`, `/scan`, wheel odometry, TF, RobotModel, and `/pose` with
fixed frame `map`. The raw `/lidar_points` display stays disabled in normal
operation. Measure Wi-Fi traffic before temporarily enabling it for alignment
debugging, then disable it again.

## Teleoperation safety sequence

1. With Robot drive power disabled, inspect `joy_enumerate_devices`, run
   `p9n_test`, and confirm `/operator/joy`. After each USB connection, press the
   controller's PS button and verify that axes leave their neutral values and
   button 4 changes while L1 is held. Do not enable drive power if messages are
   present but remain neutral; reconnect, press PS, and repeat this check.
   A USB reconnect creates a new Linux event device even when the by-id link
   resolves to the same `/dev/input/eventN`. Re-run `configure.sh` and recreate
   the Operator container before pressing PS; an existing container retains the
   stale device handle and its Joy stream eventually stops.
2. Raise the wheels. Confirm moving axes without L1 produces no nonzero command.
3. Hold L1 and test forward, reverse, left/right arcs, and in-place turns.
4. Release L1 during each motion and measure command and wheel stop times.
5. Separately unplug USB, stop teleop, and disconnect Operator Wi-Fi while moving.
6. Continue on the clear floor only after all raised-wheel stop cases pass.
7. Test R1 turbo last. L1 must remain held and the physical-stop observer stays
   beside the Robot.

Normal limits are 0.05 m/s and 0.30 rad/s; turbo limits are 0.10 m/s and
0.60 rad/s. Joy loss publishes zero after 0.25 s and the Robot controller
independently times commands out after 0.5 s. Record elapsed time until measured
wheel velocity settles to the agreed stationary threshold.

## Mapping, recovery, and shutdown

Drive a repeatable out-and-back or loop course. Capture a bag containing only
the evidence needed for TF, odometry, command, sensor, and map analysis:

```bash
ros2 bag record -o issue29-integration \
  /map /scan /sanehal_base_controller/odom \
  /sanehal_base_controller/cmd_vel /joint_states /tf /tf_static
```

Test Operator-first and Robot-first startup, teleop stop, gamepad removal,
Operator container stop, Operator Wi-Fi interruption/reconnection, JT16 loss,
and a complete cold restart. During Operator loss, Robot-local logs must prove
that `slam_toolbox`, `/scan`, and `/map` continued. Reconnect without restarting
Robot SLAM; stop the Operator ROS daemon and restart RViz only if discovery does
not recover naturally.

Save and verify the map:

```bash
mkdir -p ~/maps
ros2 run nav2_map_server map_saver_cli -f ~/maps/sanehal2 \
  --ros-args -p save_map_timeout:=10.0
test -s ~/maps/sanehal2.yaml
test -s ~/maps/sanehal2.pgm
```

Stop teleop first, verify zero wheel velocity, stop Robot launch with SIGINT,
and confirm both controllers inactive and Dynamixel torque OFF before removing
power. Record any Hesai process requiring signal escalation.

## Acceptance cases

| ID | Preconditions | Operation | Expected result | Evidence |
| --- | --- | --- | --- | --- |
| B01 | Empty Noble/Jazzy environment | import, rosdep, build, test | no missing dependency; all tests pass | versions and logs |
| B02 | No hardware | mock Robot launch test | controllers, odom, and TF appear | test result |
| R01 | Raised wheels | drive-only startup | two motors and both controllers active | hardware/controller lists |
| R02 | R01 | low-speed directions | wheel and odometry signs agree | bag and video |
| R03 | Moving raised wheels | stop commands | wheel velocity settles through 0.5 s timeout | timestamps and bag |
| L01 | JT16 connected | driver inspection | valid nonempty cloud near measured 5 Hz | fields/rate/loss |
| L02 | L01 | converter inspection | scan near cloud rate, 600 bins, valid timestamp/TF | scan sample and rate |
| L03 | Known walls/floor | compare cloud and scan | walls retained; floor/body excluded | RViz capture and bag |
| S01 | Complete Robot stack | low-speed mapping | map and full TF update continuously | bag and map capture |
| S02 | Loop/out-and-back course | return to start | no major double walls or false closure | saved map and course |
| S03 | S01 | save map | nonempty YAML/PGM reusable by map server | files and CLI log |
| O01 | Same LAN/domain/RMW | start Operator | all required remote nodes/topics discovered | graph listing |
| O02 | O01 | open RViz | map, scan, odom, TF, model, pose visible | screenshot and log |
| O03 | O02 | raw cloud off/on/off | normal view works off; bandwidth delta measured | network/topic bandwidth |
| T01 | Gamepad connected, PS pressed, live axes verified | move axes without L1 | no nonzero command or motion | command bag/video |
| T02 | L1 held | all low-speed directions | bounded TwistStamped and correct motion | command/odom bag |
| T03 | Moving | release L1 | immediate zero command and safe stop | measured stop time |
| T04 | Moving | remove USB | 0.25/0.5 s watchdog chain stops Robot | Joy/cmd/joint bag |
| F01 | Mapping | disconnect Operator Wi-Fi | Robot stops; Robot SLAM continues | Robot-local logs |
| F02 | F01 | reconnect Operator | RViz recovers without Robot restart | graph and screen recording |
| F03 | Running | disconnect JT16 | no stale scan treated as live; failure visible | topic gap and logs |
| F04 | Running | cold restart | documented sequence restores full stack | startup log and elapsed time |
| E01 | All cases passed | 30-60 minute mixed soak | no node loss, OOM, throttle, rate halt, or unbounded RSS | resource/rate log |
| X01 | Normal operation | ordered SIGINT shutdown | wheels zero, controllers stop, torque OFF | shutdown log/checklist |

The one-to-four-hour endurance test, controller overrun characterization, and
long-term thermal/memory thresholds remain in Issue #47. A short 30-60 minute
integration soak is still required here.

## Tuning and defect scope

Tune only after input rates, timestamps, QoS, and TF pass. Change one class at a
time: scan height, scan range, timestamp/TF, SLAM travel thresholds, scan
buffers/matching, then loop closure. Preserve before/after bags and maps.

Issue #29 may contain small fixes directly required by an acceptance case:
dependency metadata, names/remaps, QoS/RViz defaults, safe limits, existing
watchdogs, measured scan/SLAM parameters, tests, and this runbook. Open a
separate issue for upstream driver defects, hardware/mechanical changes, a DDS
server, command mux/Nav2 architecture, algorithm replacement, or independent
long-duration investigation. Link the reproduction, commit, impact, workaround,
and evidence from this acceptance record.

## Evidence record

Commit a concise dated result document, not large bags or raw logs. Store bags,
videos, screenshots, maps, and complete logs as Issue/PR artifacts or in the
project's controlled evidence storage. The result document must record:

- repository commit and `vcs export --exact` output;
- Robot/Operator OS, kernel, ROS/RMW/package versions and domain;
- hardware identities, network/AP configuration, clock status;
- every case as PASS, FAIL, or BLOCKED with operator and UTC timestamps;
- topic rates/bandwidth, packet-loss delta, stop times, CPU/RSS/temperature;
- links and SHA-256 values for logs, bags, maps, screenshots, and videos;
- every parameter change and linked follow-up issue.
