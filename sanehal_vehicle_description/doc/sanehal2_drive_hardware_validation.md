# SANEHAL-2 drive hardware validation (Issue #25)

This procedure is for ROS 2 Jazzy and the ROBOTIS
`dynamixel_hardware_interface`. Run the initial motion tests with the drive
wheels clear of the floor, an operator next to the power switch, and no people
or objects in the robot's path. The checked-in controller limits are 0.20 m/s
linear velocity and 1.0 rad/s angular velocity; the first commands below use
only 0.05 m/s and 0.30 rad/s.

Open a new terminal for each command group and source the workspace first:

```bash
cd ~/ws_sanehal
. /opt/ros/jazzy/setup.bash
. install/setup.bash
```

## Connection and startup

1. **Dynamixel device / port** — Confirm that the stable udev link exists and
   resolves to a serial device:

   ```bash
   ls -l /dev/dxhub
   udevadm info --query=property --name=/dev/dxhub | grep -E 'DEVNAME|ID_VENDOR|ID_MODEL|ID_SERIAL'
   test -r /dev/dxhub -a -w /dev/dxhub
   ```

2. **Left/right ID and model** — The verified SANEHAL-2 wiring uses left ID 2
   and right ID 1. Start the hardware in step 4 and record the detected model number/name for
   both IDs from the `ros2_control_node` log. Both IDs must be found exactly
   once. Compare the names/numbers with the labels or Dynamixel Wizard scan.
   Model detection is automatic; no model name is hard-coded.

3. **Baud rate** — Confirm `baud_rate` is `1000000` in
   `ros2_control/sanehal.ros2_control.xacro`. If either ID is absent, scan with
   Dynamixel Wizard at 1 Mbps before changing the repository setting. Power off
   before changing wiring.

4. **Initialize**, 5. **configure**, 6. **activate**, and 7.
   **controller_manager startup** — With wheels raised, start:

   ```bash
   ros2 launch sanehal_bringup sanehal_on_pi.launch.py
   ```

   In the log, require successful initialization, configuration, and activation
   of `sanehal_system`, followed by a running `controller_manager`. Stop here on
   a missing ID, model/control-table error, or repeated timeout. Do not send a
   velocity command to diagnose a failed lifecycle transition.

8. **Hardware components** and 9. **command/state interfaces**:

   ```bash
   ros2 control list_hardware_components -v
   ros2 control list_hardware_interfaces -v
   ```

   `Sanehal` must be `active`. Require claimed velocity command
   interfaces for `left_wheel_joint` and `right_wheel_joint`, and position and
   velocity state interfaces for both joints.

10. **joint_state_broadcaster** and 11. **diff_drive_controller**:

   ```bash
   ros2 control list_controllers
   ```

   Both `joint_state_broadcaster` and `sanehal_base_controller` must be
   `active`.

12. **`/joint_states`**:

   ```bash
   ros2 topic hz /joint_states
   ros2 topic echo --once /joint_states
   ```

   Require both wheel joint names, finite position/velocity values, and a
   stable publication rate while stationary.

13. **Velocity command method** — On ROS 2 Jazzy the controller subscribes to
   `geometry_msgs/msg/TwistStamped`. Use a bounded publisher and always send
   an explicit stop afterward:

   ```bash
   timeout 2 ros2 topic pub -r 10 /sanehal_base_controller/cmd_vel geometry_msgs/msg/TwistStamped \
     '{twist: {linear: {x: 0.0}, angular: {z: 0.0}}}'
   ros2 topic pub --once /sanehal_base_controller/cmd_vel geometry_msgs/msg/TwistStamped \
     '{twist: {linear: {x: 0.0}, angular: {z: 0.0}}}'
   ```

## Low-speed motion and direction

For steps 14–18, replace the first command's Twist with each value below. Run
only one test at a time for two seconds, then send the explicit zero command
from step 13. First run with wheels raised; repeat on the floor only after step
19 passes.

14. **Forward:** `{linear: {x: 0.05}, angular: {z: 0.0}}`
15. **Reverse:** `{linear: {x: -0.05}, angular: {z: 0.0}}`
16. **Left turn:** `{linear: {x: 0.05}, angular: {z: 0.30}}`
17. **Right turn:** `{linear: {x: 0.05}, angular: {z: -0.30}}`
18. **In-place turn:** `{linear: {x: 0.0}, angular: {z: 0.30}}`, then repeat
    with `z: -0.30`.

19. **Wheel direction** — Viewed in the robot base frame, positive linear x
    must rotate both wheels toward forward travel. A positive angular z command
    must drive the right wheel forward and the left wheel backward. Confirm that
    the signs in `/joint_states` follow each joint axis in the URDF. If a side is
    reversed, inspect the motor mounting and the sign entries in both
    transmission matrices; do not use a negative wheel-radius multiplier.

## Odometry, errors, and calibration

20. **`/odom`**:

   ```bash
   ros2 topic hz /sanehal_base_controller/odom
   ros2 topic echo /sanehal_base_controller/odom
   ```

   Require continuous finite pose/twist values and forward x growth for a
   forward command.

21. **Straight distance comparison** — Mark a start line, drive straight at
   0.05 m/s over a measured 1.0 m (stop early if unsafe), and record actual
   distance `D_actual` and odometry displacement `D_odom`. Repeat at least three
   times in both directions.

22. **Turn-angle comparison** — Mark the chassis heading, perform a slow
   in-place 360-degree turn in each direction, and compare actual unwrapped
   angle `A_actual` with odometry angle `A_odom`. Repeat at least three times.

23. **Communication errors / timeout** — During stationary and motion tests,
   watch the launch terminal and check kernel messages:

   ```bash
   journalctl -k --since '10 minutes ago' | grep -Ei 'ttyUSB|usb|ftdi|disconnect|error'
   ```

   Any repeating packet error, missing status packet, 500 ms timeout, USB
   disconnect, controller deactivation, or non-finite joint state is a failure.
   Check power, common ground, connectors, udev permissions, baud rate, and ID
   uniqueness before retrying.

24. **Calibration when required** — Keep motor direction in the transmission
   matrices. Starting from the current multipliers, calculate:

   - common wheel-radius multiplier = old multiplier × `D_actual / D_odom`
   - wheel-separation multiplier = old multiplier × `A_odom / A_actual`

   Apply the common radius correction first, rebuild/restart, repeat the
   straight test, then apply separation correction and repeat the turn test.
   Use separate left/right radius multipliers only for a repeatable straight
   drift, changing them in small steps. Record raw trials and final values in
   Issue #25; do not tune using a single run.
