# SANEHAL-2 bringup

## JT16 2D SLAM

Install the repository udev rules before starting the hardware. They create
`/dev/jt16_rs485` for the point cloud stream, `/dev/jt16_rs232` for commands
and angle calibration, and `/dev/dxhub` for the wheel motors:

```bash
sudo usermod -aG dialout "$USER"
sudo cp dev_rules/*.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
ls -l /dev/jt16_rs485 /dev/jt16_rs232 /dev/dxhub
```

Log out and back in after adding the user to `dialout`.

`jt16.launch.py` starts the official Hesai ROS 2 driver with
`config/jt16_serial.yaml`. `sanehal.launch.py` is the Robot-side entry point and
starts drive/TF, JT16, PointCloud2-to-LaserScan, and `slam_toolbox`; pass
`start_lidar:=false` when the driver is already running. The driver publishes
`sensor_msgs/msg/PointCloud2` on
`/lidar_points` with `frame_id: hesai_lidar`.

```bash
. install/setup.bash
ros2 launch sanehal_bringup jt16.launch.py
# Start the complete Robot-side stack on the Raspberry Pi (RViz stays off):
ros2 launch sanehal_bringup sanehal.launch.py
```

On an Operator workstation, use the separate `sanehal_operator` package. It
starts only RViz and consumes the description, TF, and sensor topics published
by the Raspberry Pi. It does not start a hardware interface, controller, or
additional robot-state publisher:

```bash
ros2 launch sanehal_operator operator.launch.py
```

The display-only launch defaults to `map`. Use `fixed_frame:=odom` only when
`slam_toolbox` is intentionally disabled and `map -> odom` is unavailable.

The upstream v2.0.12 point-cloud publisher uses Reliable/Volatile QoS with a
depth of 10. Its cloud header uses the frame start time. The checked-in config
uses the host receive timestamp (`use_timestamp_type: 1`) until the JT16 clock
has been synchronized and its device timestamp has been validated. The RS232
port supplies commands and angle calibration; if it is unavailable, configure
a valid `correction_file_path` instead of leaving it empty, then launch with
`require_jt16_rs232:=false`. The RS485 data port remains mandatory.

`pointcloud_to_laserscan.launch.py` converts `/lidar_points` to `/scan` using
`config/pointcloud_to_laserscan_jt16.yaml`. It preserves the cloud timestamp and
`hesai_lidar` frame. The converter subscribes to the cloud only while `/scan`
has a subscriber, so use `ros2 topic echo`, RViz, or `slam_toolbox` when testing
it by itself.

`slam.launch.py` is retained as a compatibility wrapper for the integrated
`sanehal.launch.py`. Disable components that are already running to avoid
duplicate publishers:

```bash
. install/setup.bash
ros2 launch sanehal_bringup slam.launch.py
# Converter only:
ros2 launch sanehal_bringup pointcloud_to_laserscan.launch.py
# Reuse an externally started robot, JT16 driver, and converter:
ros2 launch sanehal_bringup slam.launch.py \
  start_robot_bringup:=false start_lidar:=false \
  start_pointcloud_to_laserscan:=false
```

The Robot-side component switches are `start_description`, `start_control`,
`start_lidar`, `start_pointcloud_to_laserscan`, and `start_slam`.
RViz belongs to `sanehal_operator` and never runs from Robot bringup. Config
paths and `/lidar_points`/`/scan` topic names are launch arguments.
`use_mock_hardware:=true` selects the
ros2_control GenericSystem only for hardware-free tests; production always uses
ROBOTIS `dynamixel_hardware_interface`.

For drive/TF diagnostics without serial devices:

```bash
ros2 launch sanehal_bringup sanehal.launch.py use_mock_hardware:=true \
  start_lidar:=false start_pointcloud_to_laserscan:=false start_slam:=false
```

For description and static TF only, also pass `start_control:=false`. Device
checks wait up to `device_wait_timeout` seconds and can be bypassed for an
intentional external-data workflow with `wait_for_devices:=false`.

The main launch arguments and defaults are:

| Argument | Default | Purpose |
| --- | --- | --- |
| `use_mock_hardware` | `false` | Select GenericSystem for hardware-free tests |
| `start_description` / `start_control` | `true` | Robot model/TF and drive stack |
| `start_lidar` / `start_pointcloud_to_laserscan` | `true` | JT16 cloud and 2D scan |
| `start_slam` | `true` | Online asynchronous `slam_toolbox` |
| `wait_for_devices` | `true` | Check serial device access before node startup |
| `device_wait_timeout` | `10.0` | Device wait timeout in seconds |
| `require_jt16_rs232` | `true` | Require the JT16 command port; disable only with a correction file |
| `dynamixel_port` / `dynamixel_baud_rate` | `/dev/dxhub` / `1000000` | ROBOTIS hardware connection |
| `pointcloud_topic` / `scan_topic` | `/lidar_points` / `/scan` | Sensor contracts |

`jt16_rs485_device` and `jt16_rs232_device` are preflight paths and must match
the paths in the selected `jt16_config_file`. The standalone `jt16.launch.py`
uses the equivalent `require_rs232` argument.

## Robot/Operator interface contract

Set the same non-conflicting `ROS_DOMAIN_ID` on the Raspberry Pi and Operator
PC. The Robot publishes `/map`, `/scan`, `/sanehal_base_controller/odom`,
`/joint_states`, `/tf`, `/tf_static`, and `/robot_description`. `/lidar_points`
is a high-bandwidth debug topic and need not be displayed during normal
operation. `/lidar_imu` remains disabled until its hardware data contract is
validated.

Teleoperation sends `geometry_msgs/msg/TwistStamped` to
`/sanehal_base_controller/cmd_vel`. The Robot-side controller timeout is 0.5 s;
the Operator-side implementation in Issue #41 must also require a deadman
button. A future teleop/Nav2 mux belongs upstream of this controller input.

Inspect the raw JT16 contract before starting the converter:

```bash
ros2 topic info /lidar_points --verbose
ros2 topic hz /lidar_points
ros2 topic bw /lidar_points
ros2 topic echo /lidar_points --once --field header
ros2 run tf2_ros tf2_echo base_link hesai_lidar
```

The expected PointCloud2 fields are `x`, `y`, `z`, `intensity`, `ring`, and
`timestamp`. The nominal frame rate is 10 Hz. Confirm the actual rate, nonzero
point count, timestamp latency, packet loss, and point-cloud alignment on the
robot. `/lidar_imu` is disabled by default: enable it only after confirming the
JT16 hardware supplies usable IMU samples and validating their rate, units,
timestamp, and covariance limitations.

If the SANEHAL-2 base is already running, avoid duplicate controller and TF
publishers:

```bash
ros2 launch sanehal_bringup sanehal.launch.py \
  start_control:=false start_description:=false
```

The live TF ownership is:

- `slam_toolbox`: `map -> odom`
- `sanehal_base_controller` (`diff_drive_controller`): `odom -> base_footprint`
- `robot_state_publisher`: `base_footprint -> base_link -> sanehal_base_link -> hesai_lidar`

Do not add a static `map -> odom` or `odom -> base_footprint` publisher. Before
driving, confirm `/scan`, `/sanehal_base_controller/odom`, and the complete TF
chain:

```bash
ros2 topic info /scan --verbose
ros2 topic hz /scan
ros2 topic hz /sanehal_base_controller/odom
ros2 run tf2_ros tf2_echo base_link hesai_lidar
ros2 run tf2_ros tf2_echo odom base_footprint
ros2 run tf2_ros tf2_echo map odom
ros2 topic echo /map --once
```

JT16 projects a 3D cloud into one planar scan. The initial sensor-frame height
slice is `[-0.05, 0.05]` m, and the initial limits are `range_min: 0.3` m and
`range_max: 30.0` m (the JT16 manual specifies a shorter minimum instrumented
range and 30 m capability at 10% reflectivity). The 360-degree output uses the
nominal 0.6-degree JT16 horizontal resolution. Jazzy
slam_toolbox 2.8.4 does not declare the old `min_laser_range` and
`max_laser_range` parameters still shown in its example YAML, so the effective
limits must come from the generated `LaserScan.range_min`/`range_max`. Select
the height band so floor, ceiling, and the robot body are excluded; preserve
the cloud timestamp; and verify that the scan's `hesai_lidar` frame has a TF at
that timestamp. Empty or sparse height slices and delayed timestamps commonly
look like SLAM or TF failures.

The configured `scan_time: 0.2` is metadata for the 5 Hz cloud rate measured
on the SANEHAL-2 JT16 serial connection; it does not throttle conversion.
Missing angular bins are published as `+inf`, `time_increment` is zero, and the
converter does not populate LaserScan intensities. Keep
`queue_size: 1` initially to avoid accumulating stale point clouds. On the
Raspberry Pi and over Wi-Fi, display the raw PointCloud2 only while debugging;
its serialization and transport can materially increase CPU and bandwidth.

For offline tuning, record only the required high-bandwidth and TF topics:

```bash
ros2 bag record -o jt16_issue31 /lidar_points /tf /tf_static \
  /sanehal_base_controller/odom
ros2 bag play jt16_issue31 --clock
ros2 launch sanehal_bringup pointcloud_to_laserscan.launch.py use_sim_time:=true
```

Compare the cloud and scan rates, header stamps and frames, finite/`+inf` bin
counts, minimum/maximum finite ranges, and CPU load. Tune the height slice
first, then range limits. Widen `queue_size` only if drops are unacceptable and
processing latency remains bounded.

Save the occupancy map for Nav2 after mapping:

```bash
ros2 run nav2_map_server map_saver_cli -f ~/maps/sanehal2 \
  --ros-args -p save_map_timeout:=10.0
```

Issue #29 performs the final hardware mapping test. Tune there only after the
input and TF checks pass: projection height limits and range limits first,
then `minimum_travel_distance`, `minimum_travel_heading`,
`minimum_time_interval`, `transform_timeout`, scan buffer sizes, scan matching
response thresholds, and loop-closure search/response thresholds. Also verify
map consistency during straight and turning motion, wheel odometry scale and
drift, scan density/rate, timestamp latency, CPU load, false loop closures, and
map-save output.
