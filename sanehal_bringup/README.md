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
`config/jt16_serial.yaml`. `sanehal.launch.py` starts both the drive/TF stack
and the JT16 driver; pass `start_lidar:=false` when the driver is already
running. The driver publishes `sensor_msgs/msg/PointCloud2` on
`/lidar_points` with `frame_id: hesai_lidar`.

```bash
. install/setup.bash
ros2 launch sanehal_bringup jt16.launch.py
# Or start the robot and JT16 together on the Raspberry Pi:
ros2 launch sanehal_bringup sanehal.launch.py
```

On a workstation, start only RViz and consume the robot description, TF, and
sensor topics published by the Raspberry Pi. This launch does not start a
hardware interface, controller, or additional robot-state publisher:

```bash
ros2 launch sanehal_bringup sanehal_rviz.launch.py
```

The display-only launch overrides the RViz fixed frame to `odom`, which is
published by the Raspberry Pi vehicle stack. Use `fixed_frame:=map` when
`slam_toolbox` is running and the `map -> odom` transform is available.

The upstream v2.0.12 point-cloud publisher uses Reliable/Volatile QoS with a
depth of 10. Its cloud header uses the frame start time. The checked-in config
uses the host receive timestamp (`use_timestamp_type: 1`) until the JT16 clock
has been synchronized and its device timestamp has been validated. The RS232
port supplies commands and angle calibration; if it is unavailable, configure
a valid `correction_file_path` instead of leaving it empty.

`pointcloud_to_laserscan.launch.py` converts `/lidar_points` to `/scan` using
`config/pointcloud_to_laserscan_jt16.yaml`. It preserves the cloud timestamp and
`hesai_lidar` frame. The converter subscribes to the cloud only while `/scan`
has a subscriber, so use `ros2 topic echo`, RViz, or `slam_toolbox` when testing
it by itself.

`slam.launch.py` starts the SANEHAL-2 drive/TF stack, JT16 driver,
PointCloud2-to-LaserScan converter, Jazzy `slam_toolbox` in online asynchronous
mapping mode, and RViz. Disable components that are already running to avoid
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

The Robot-side bringup interface passed to Issue #27 is `start_lidar`,
`start_pointcloud_to_laserscan`, `jt16_config_file`, `converter_params_file`,
`pointcloud_topic`, `scan_topic`, and `use_sim_time`. The topic arguments are
implemented as remaps; their defaults are `/lidar_points` and `/scan`.

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
ros2 launch sanehal_bringup slam.launch.py start_robot_bringup:=false
```

The live TF ownership is:

- `slam_toolbox`: `map -> odom`
- `sanehal_base_controller` (`diff_drive_controller`): `odom -> base_link`
- `robot_state_publisher`: `base_link -> sanehal_base_link -> hesai_lidar`

Do not add a static `map -> odom` or `odom -> base_link` publisher. Before
driving, confirm `/scan`, `/sanehal_base_controller/odom`, and the complete TF
chain:

```bash
ros2 topic info /scan --verbose
ros2 topic hz /scan
ros2 topic hz /sanehal_base_controller/odom
ros2 run tf2_ros tf2_echo base_link hesai_lidar
ros2 run tf2_ros tf2_echo odom base_link
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

The configured `scan_time: 0.1` is metadata for the nominal 10 Hz cloud rate;
it does not throttle conversion. Change it to `0.2` if hardware measurement
shows 5 Hz. Missing angular bins are published as `+inf`, `time_increment` is
zero, and the converter does not populate LaserScan intensities. Keep
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
