# SANEHAL-2 Operator

This package contains Operator-side monitoring and opt-in USB PlayStation
gamepad teleoperation. It never starts Robot hardware, `robot_state_publisher`,
the JT16 driver, scan conversion, or `slam_toolbox`.

## ROS interface contract

The Raspberry Pi runs `sanehal_bringup/sanehal.launch.py`. The Operator consumes:

| Interface | Purpose | RViz QoS |
| --- | --- | --- |
| `/map` | `slam_toolbox` occupancy grid | Reliable, Transient Local |
| `/scan` | JT16-derived 2D scan | Best Effort, Volatile, depth 5 |
| `/sanehal_base_controller/odom` | Wheel odometry | Reliable, Volatile |
| `/pose` | `slam_toolbox` pose with covariance | Reliable, Volatile |
| `/tf`, `/tf_static` | Complete `map` to sensor TF tree | ROS TF defaults |
| `/robot_description` | RobotModel source | Reliable, Transient Local |
| `/lidar_points` | Raw JT16 cloud, debug only | Best Effort, depth 1 |

The PointCloud2 display is disabled by default because it can materially load
the Raspberry Pi, Wi-Fi link, and Operator GPU. Enable it temporarily for sensor
alignment or projection debugging and compare `ros2 topic bw /lidar_points`.

## Network contract

Robot and Operator must use ROS 2 Jazzy, the same non-conflicting
`ROS_DOMAIN_ID`, and `rmw_fastrtps_cpp`. The default deployment uses DDS subnet
discovery and Docker host networking on the Linux Operator host:

```bash
export ROS_DOMAIN_ID=42                 # choose for the deployment
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
export ROS_LOCALHOST_ONLY=0
```

Do not copy the example domain blindly when another ROS system shares the LAN.
No IP address or NIC name is built into the image. If the WLAN blocks multicast,
set `ROS_STATIC_PEERS` at deployment time on both ends, or deploy a Fast DDS
Discovery Server and document its stable hostname outside the image.

The access point must not isolate wireless clients. Limit firewall rules to the
trusted LAN and the DDS UDP ports for the selected domain. Keep Robot and
Operator clocks synchronized with chrony or systemd-timesyncd; timestamp skew
commonly appears as an RViz TF error.

## Container startup on Ubuntu 26.04

The host supplies Docker, networking, time, display sockets, and `/dev/dri`.
ROS 2 runs in the Ubuntu 24.04/Jazzy image.

```bash
ROS_DOMAIN_ID=42 scripts/operator/configure.sh
scripts/operator/up.sh
```

RViz on Jazzy uses OGRE/GLX, so `up.sh` uses X11 on an Xorg session and XWayland
on a Wayland session. It creates a private Xauthority file containing only the
current display cookie; it never runs `xhost +` and does not expose the Wayland
runtime directory. `up.sh` adds `compose.operator.gpu.yaml` only when `/dev/dri`
exists, otherwise it selects Mesa software rendering. For manual startup, add
exactly one of `compose.operator.gpu.yaml` or
`compose.operator.software-rendering.yaml` after the X11 override.

Normal operation does not require VS Code. For development, run
`scripts/operator/configure.sh` first, then open the repository with
**Dev Containers: Reopen in Container**. The Dev Container uses the current
authenticated X11/XWayland display so the same environment can launch RViz.
`.devcontainer/devcontainer.json` attaches to the same `operator` service and
Dockerfile, adding the display override, portable software rendering, source
mount, build volumes, and an idle development command. The image seeds the
named build/install/log volumes with the Operator UID/GID. Install host package
`xauth` if it is absent. Developers can replace the software override with the
GPU override when hardware acceleration is required.

The default `.devcontainer/devcontainer.json` remains the monitoring-only
development environment. For gamepad development, first run `configure.sh` with
`GAMEPAD_BY_ID` and then open `.devcontainer/gamepad/devcontainer.json`; this
adds the same minimal USB event-device override while retaining the source and
build-volume mounts. Its development command remains `sleep infinity`, so start
teleop explicitly after building:

```bash
. install/setup.bash
ros2 launch sanehal_operator operator.launch.py \
  enable_teleop:=true gamepad_model:=DualSense
```

The base image is pinned by digest in the Dockerfile, Compose default, and
`.env.example`. To update it, resolve the new `osrf/ros:jazzy-desktop` digest,
change all three references together, rebuild without relying on the old base,
and rerun package tests plus LAN/RViz smoke tests. ROS deb packages are refreshed
only when that image layer is intentionally rebuilt; record their versions from
`dpkg-query` with the test results.

## Direct ROS launch

Inside a configured Jazzy environment:

```bash
. install/setup.bash
ros2 launch sanehal_operator operator.launch.py
# When slam_toolbox is intentionally disabled:
ros2 launch sanehal_operator operator.launch.py fixed_frame:=odom
```

## Diagnostics

Run checks in this order so network, DDS, QoS, TF/time, and GUI failures do not
get conflated:

```bash
# Host/LAN
ip -brief address
ip route
ping -c 3 <robot-hostname>
timedatectl status

# Discovery and interfaces (inside the Operator container)
ros2 daemon stop
ros2 node list
ros2 topic list -t
ros2 service list -t
ros2 action list -t
ros2 lifecycle get /slam_toolbox

# QoS, rate, and bandwidth
ros2 topic info /map --verbose
ros2 topic info /scan --verbose
ros2 topic info /lidar_points --verbose
ros2 topic info /sanehal_base_controller/odom --verbose
ros2 topic echo /map --once
ros2 topic hz /scan
ros2 topic bw /scan
ros2 topic bw /lidar_points

# TF and SLAM
ros2 run tf2_ros tf2_echo map odom
ros2 run tf2_ros tf2_echo odom base_footprint
ros2 run tf2_ros tf2_echo base_link hesai_lidar
ros2 topic echo /pose --once
ros2 service type /slam_toolbox/dynamic_map
ros2 service call /slam_toolbox/dynamic_map nav_msgs/srv/GetMap '{}'
```

If no remote nodes appear, compare domain, RMW, discovery range, firewall, and
AP client-isolation settings before investigating RViz. If CLI topics work but
RViz does not, inspect the Wayland/X11 socket, Xauthority, `/dev/dri` ownership,
and `glxinfo -B`.

For a Wi-Fi recovery test, keep the Robot console visible, disconnect only the
Operator network, and confirm `/map`, `/scan`, and the active `slam_toolbox`
lifecycle continue on the Raspberry Pi. Reconnect, run `ros2 daemon stop`, and
restart RViz if its DDS graph cache does not recover. The Robot SLAM process must
not be restarted.

## USB PlayStation gamepad teleoperation

Supported models are `DualShock3`, `DualShock4`, and `DualSense`. The gamepad
uses a USB data cable connected to the Ubuntu 26.04 host. The host owns USB,
udev, and the kernel HID/input drivers; Bluetooth, BlueZ, and D-Bus are not part
of this path and are not exposed to the container.

Identify the controller before configuration:

```bash
lsusb
cat /proc/bus/input/devices
ls -l /dev/input/by-id/*-event-joystick
udevadm info --query=property --name=/dev/input/eventN
```

Use the controller's stable `*-event-joystick` link, not a guessed `eventN`.
The configuration script resolves that link, verifies a readable character
device, and records its current path and group GID. Compose maps only that event
device read-only and adds only its GID. It does not use `privileged: true` or
expose `/dev`, `/dev/input`, the USB bus, or host D-Bus.

```bash
ROS_DOMAIN_ID=42 \
GAMEPAD_BY_ID=/dev/input/by-id/<controller>-event-joystick \
GAMEPAD_MODEL=DualSense \
scripts/operator/configure.sh
scripts/operator/up.sh
```

Valid model values are exactly `DualShock3`, `DualShock4`, and `DualSense`.
Before allowing wheel motion, verify the SDL device and the selected p9n mapping
inside the container:

```bash
ros2 run joy joy_enumerate_devices
ros2 launch p9n_test test.launch.py hw_type:=DualSense
ros2 topic echo /operator/joy
```

The SANEHAL node reuses `p9n_interface::PlayStationInterface`; raw Linux axis
and button numbers are not duplicated in this package. L1 is the default
hold-to-run deadman and R1 enables turbo only while L1 remains held. The default
normal limits are 0.05 m/s and 0.30 rad/s; turbo is 0.10 m/s and 0.60 rad/s.
The node publishes `geometry_msgs/msg/TwistStamped` directly to
`/sanehal_base_controller/cmd_vel`. It must be the only publisher on that topic:

```bash
ros2 topic info /sanehal_base_controller/cmd_vel --verbose
```

The Operator Joy watchdog publishes zero after 0.25 seconds without input. The
Robot controller independently rejects commands after 0.5 seconds. Releasing
L1 publishes zero immediately. Neither timeout replaces a physical emergency
stop or an operator next to the Robot power switch during initial tests.

For a direct launch inside a configured container:

```bash
. /opt/sanehal_operator_ws/install/setup.bash
ros2 launch sanehal_operator operator.launch.py \
  enable_teleop:=true gamepad_model:=DualSense
```

USB removal must stop the Robot. If reconnection creates a different `eventN`,
the existing Docker device mapping cannot follow it. Re-run `configure.sh` and
recreate the service with `up.sh`. Do not broaden device access to avoid this
explicit recovery step. A charge-only cable will power a controller without
creating an input device; use a known USB data cable. Secure the cable so it
cannot enter the wheels or pull the Operator PC.

### Staged hardware validation

1. Verify `/operator/joy` and run `p9n_test` with Robot drive power disabled.
2. Raise and securely support the wheels; keep hands and cables clear.
3. Confirm no movement without L1, then test forward, reverse, left, right, and
   in-place turns at normal speed.
4. Release L1 during each motion and measure the stop response.
5. While commanding motion, unplug USB, stop the container, and disconnect the
   Operator network separately. Each test must stop through the 0.25/0.5 second
   timeout chain.
6. Only after direction and stopping pass, repeat at low speed on a clear floor.
7. Test turbo last, with an operator beside the Robot power switch.

The current system has no keyboard, Nav2, or mux command source. Before adding
one, keep each source on a separate topic and add a Robot-side TwistStamped
arbiter; only that arbiter may then publish to the controller input.
