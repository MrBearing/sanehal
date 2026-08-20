# SANEHAL-2 bringup

## JT16 2D SLAM

`slam.launch.py` starts the SANEHAL-2 drive/TF stack, Jazzy
`slam_toolbox` in online asynchronous mapping mode, and RViz. The JT16 driver
and `pointcloud_to_laserscan` are supplied by Issues #30, #31, and #27; start
that sensor path first so that it publishes `/lidar_points` and `/scan` with
`frame_id: hesai_lidar`. The legacy LD19 launch is intentionally not included.

```bash
. install/setup.bash
ros2 launch sanehal_bringup slam.launch.py
```

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

JT16 projects a 3D cloud into one planar scan. In Issue #31, initially use
`range_min: 0.3` m and `range_max: 30.0` m (the JT16 manual specifies a 0.15 m
minimum instrumented range and 30 m capability at 10% reflectivity). Jazzy
slam_toolbox 2.8.4 does not declare the old `min_laser_range` and
`max_laser_range` parameters still shown in its example YAML, so the effective
limits must come from the generated `LaserScan.range_min`/`range_max`. Select
the height band so floor, ceiling, and the robot body are excluded; preserve
the cloud timestamp; and verify that the scan's `hesai_lidar` frame has a TF at
that timestamp. Empty or sparse height slices and delayed timestamps commonly
look like SLAM or TF failures.

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
