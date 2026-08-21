# SANEHAL-2 Operator

This package contains only Operator-side monitoring. It starts RViz and never
starts Robot hardware, `robot_state_publisher`, the JT16 driver, scan conversion,
or `slam_toolbox`.

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
runtime directory. To diagnose a GPU driver problem, add
`-f compose.operator.software-rendering.yaml` to a manual Compose invocation.

Normal operation does not require VS Code. For development, run
`scripts/operator/configure.sh` first, then open the repository with
**Dev Containers: Reopen in Container**. The Dev Container uses the current
authenticated X11/XWayland display so the same environment can launch RViz.
`.devcontainer/devcontainer.json` attaches to the same `operator` service and
Dockerfile, adding only the display override, source mount, build volumes, and
an idle development command. Install host package `xauth` if it is absent.

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

## Issue #41 extension

Teleoperation should extend this image and network contract with a separate
Compose override. Map only the selected `/dev/input/event*` or `/dev/input/js*`
device and add its `input` group GID; do not use `privileged: true` or expose all
of `/dev/input`. The Robot controller accepts `TwistStamped` on
`/sanehal_base_controller/cmd_vel` and retains its 0.5 second timeout.
