# Issue #29 integration result — 2026-08-24

Status: **IN PROGRESS — functional integration passed; RViz #53 and Operator trend evidence remain**

## Baseline

- Source branch: `feature/issue-29-system-integration`
- Base commit: `ab6577caec200f42c2add3b93de15de7e9507b12`
- Operator host: `melon`, x86_64, Ubuntu Resolute kernel 7.0
- Clean validation: `osrf/ros:jazzy-desktop` (Ubuntu 24.04 / Jazzy)
- Robot: `sanehal-pi5`, aarch64 Raspberry Pi kernel 6.8.0-1061-raspi
- Observation time: 2026-08-24 15:47 JST

The final tested commit and artifact hashes must be filled after the acceptance
run. Large logs, bags, maps, screenshots, and videos are not stored in Git.

## Automated results

| Case | Result | Evidence / notes |
| --- | --- | --- |
| B01 clean dependency import | PASS | all five repositories checked out at the revisions in `build_depends.repos`; Hesai SDK submodule `9d5dc4fc4ade5be5f6a6ca00e71dd4050b054168` |
| B01 rosdep | PASS | all required rosdeps installed after removing invalid `mock_components`; Hesai undeclared Boost/YAML dependencies installed explicitly |
| B01 clean build | PASS | 16 packages finished in the disposable Noble/Jazzy container |
| B01 tests | PASS | 200 tests collected; functional/launch tests passed; the only initial failure was import-order lint in the new contract test, which was corrected and rerun successfully |
| Repository contracts | PASS | 13 direct pytest checks passed |
| Shell/diff validation | PASS | `bash -n` and `git diff --check` passed |
| Operator Compose expansion | PASS | domain 42, Fast DDS, SUBNET discovery, event9-only device mapping, and input group addition confirmed; no privileged device exposure |
| L01 JT16 smoke | PASS | Robot-local driver produced Reliable/Volatile PointCloud2 at 4.985-4.988 Hz, frame `hesai_lidar`, normally 9,600 points/frame; packet counter 61,395 with zero loss |
| Pi feature build/test | PASS | 9 packages built on aarch64; 55 tests, 0 errors/failures, 2 skipped |
| R01 controllers/hardware | PASS | official ROBOTIS hardware active; both controllers active; joint states about 100 Hz and odom about 50 Hz |
| R02 raised-wheel directions | PASS | forward `[+1.246,+1.222]`, reverse `[-1.222,-1.222]`, left `[-0.743,+0.719]`, right `[+0.743,-0.719]` rad/s |
| R03 command timeout | PASS | both measured wheel velocities were 0.0 one second after command publication stopped |
| S01 stationary full stack | PASS | `slam_toolbox` active; cloud/scan about 4.987 Hz; odom about 50 Hz; map 71x85 at 0.05 m; complete TF available |
| S03 map save/reload smoke | PASS | saved 73x85 map; YAML `add5112...addf`, PGM `d77d55...9e3b`; separate lifecycle map server loaded and published it |
| O01 Operator discovery | PASS with recovery step | remote map/scan/odom/TF/lifecycle available after `ros2 daemon stop` and graph rediscovery |
| O02 RViz startup | FAIL | RobotModel/map data received, but OccupancyGrid GLSL link error occurs with GPU and software rendering; tracked by #53 |
| T01 no-deadman idle | PASS | physical Joy messages observed with all buttons released and no nonzero command/motion observed |
| T02 low-speed directions | PASS | raised-wheel run reached linear `-0.05..+0.05 m/s`, angular `-0.30..+0.30 rad/s`, and wheel velocity `-1.246..+1.270 rad/s`; forward/reverse and left/right signs observed |
| T03 deadman release | PASS | L1 was button 4; command reached zero in 44 ms and measured wheel velocity settled below 0.05 rad/s in 350 ms |
| T04 gamepad USB removal | PASS | Joy stream ended during forward input; command reached zero in 40 ms and measured wheel velocity settled below 0.05 rad/s in 350 ms |
| S02 first floor course | INVALID | test bench was too narrow and the Robot was obstructed by a carpet edge; although it physically returned near its start, map/odom evidence cannot be used for unconstrained-course acceptance |
| Wheel-separation calibration | PASS | unobstructed physical 360-degree turns measured 366.23 degrees left and 368.14 degrees right in wheel odometry; multiplier corrected from 1.00 to 1.02 |
| S02 calibrated floor course | FAIL, tuning required | wheel odometry returned within 0.017 m / 13.3 degrees, but SLAM correction ended at 0.439 m / 30.5 degrees and the map showed duplicate walls |
| S02 tuned floor course | PASS with residual | 2.30 m flat-floor out-and-back; wheel odometry closed to 0.118 m / 5.3 degrees and SLAM to 0.374 m / 9.3 degrees; major wall structure remained coherent, with short-course position error retained as a risk |
| F01/F02 Operator Wi-Fi loss/rejoin | PASS | Wi-Fi unavailable for 14.44 s; wheels settled below 0.05 rad/s 0.721 s after link loss, while Robot produced 72 scans and 3 maps; no command resumed for 181 s after reconnection |
| E01 30-minute Robot soak | PASS | 1798.5 s, scan 4.986 Hz, map 0.201 Hz, odom 50.0 Hz, joints 100.0 Hz; no node/controller loss, OOM, swap, or unbounded Hesai/SLAM RSS growth |
| Operator participant loss/rejoin | PASS | container stop left Robot SLAM active and scan near 4.99 Hz; restart recovered map, lifecycle, and TF without Robot restart |
| Ordered shutdown | PASS with warning | both Dynamixels Torque OFF; hardware deactivate/shutdown successful; controller statistics thread logs an error after context invalidation |

Upstream `p9n_*` packages emit scoped-header installation warnings for future
ROS distributions. They do not fail the Jazzy build and are outside #29.

## Hardware readiness observation

| Item | Observed | Gate |
| --- | --- | --- |
| Robot ROS | `/opt/ros/jazzy/setup.bash` present | PASS |
| Robot serial devices | `/dev/dxhub`, `/dev/jt16_rs485`, `/dev/jt16_rs232`, all `crw-rw-rw- root:dialout` | PASS |
| Robot time | Asia/Tokyo, NTP synchronized | PASS |
| Robot resources | 15 GiB RAM, 13 GiB available, swap unused, load 0.28/0.25/0.33 | PASS |
| Existing ROS processes | none observed | PASS |
| Robot source | feature branch deployed at `c15de5e`; untracked `AGENTS.md` and `test_jt16.bash` preserved | PASS |
| Operator gamepad | USB Sony PLAYSTATION 3, stable by-id link to event9 | PASS |
| Operator domain | 61 | PASS |
| Robot domain | 61 in `.bashrc` | PASS |
| Physical safety | user confirmed raised wheels, exclusion control, observer, and physical stop readiness before motion | PASS (operator attestation) |

The Pi initially lacked the #41 PlayStation source dependency. Importing the
manifest also exposed a migration-path mismatch: the existing Hesai checkout
was named `HesaiLidar_ROS_2.0`, while the manifest key requested
`hesai_lidar_ros2`, producing a duplicate ROS package. The manifest key was
aligned to the existing standard workspace path; the newly created duplicate
was moved out of the workspace without altering the original checkout.

The JT16-only smoke test did not start ros2_control or send motor commands. The
driver process was absent after the bounded SIGINT/TERM/KILL cleanup. The log
did not identify which signal completed shutdown, so graceful Hesai shutdown
remains to be measured in X01.

The Robot is reachable as `sanehal-pi5.local` at the observed address
192.168.68.72. The bare hostname temporarily failed DNS lookup; mDNS succeeded.
Use the hostname, not the observed DHCP address, in operational instructions.

## Required actions before R01

- [ ] Choose one non-conflicting domain and set it identically on Robot and Operator.
- [ ] Deploy or otherwise make this issue branch available in the existing Pi
      repository without modifying its untracked user files.
- [ ] Build and test that exact source on Pi.
- [ ] Confirm wheels are securely raised and cables cannot reach them.
- [ ] Place an observer beside the physical power/emergency-stop control.
- [ ] Record Robot and Operator clock skew and firewall/AP client-isolation state.

The source/domain/build gates were subsequently cleared: both sides used domain
61, and the Pi ran commit `c15de5e` while preserving its two untracked files.
The build required adding the missing PlayStation dependency. An accidental
symlink-build cache conflict was recovered without deleting source or install;
the old affected cache is retained at
`/tmp/issue29-build-backup-20260824T065545Z` on the Pi.

The first physical gamepad capture contained Joy messages but all axes remained
at their inactive values because the DualShock 3 had not been activated with
the PS button. It produced no motion and is not accepted as T02-T04 evidence.
After reconnecting and pressing PS, live axis changes and L1 as button 4 were
verified before repeating the cases. The accepted bag is
`~/maps/issue29/teleop-raised-valid-20260824` on the Robot: 180.4 seconds,
29,893 messages, metadata SHA-256 `a7d33357...73c95`, MCAP SHA-256
`fc266201...d8f7`. This activation check is now part of the runbook.

The first floor course produced a 134x104 map and continuous valid scan data,
but it is not an acceptance result: the narrow test bench and a carpet edge
constrained the Robot. Its bag remains at
`~/maps/issue29/floor-course-20260824` for diagnosis. A subsequent unobstructed
turn calibration gave consistent separation multipliers of 1.0174 and 1.0228
for physical left/right 360-degree turns. The controller uses their rounded
mean, `wheel_separation_multiplier: 1.02`. The calibration bag is
`~/maps/issue29/turn-calibration-20260824`, metadata SHA-256
`704f3d91...37b0`, MCAP SHA-256 `f892cca0...9d30`.

After calibration, the valid two-metre out-and-back wheel odometry closed to
0.017 m and 13.3 degrees. Scan matching degraded that result to 0.439 m and
30.5 degrees in `map -> base`, with visible duplicate walls. The scan itself
was dense (median 599 of 600 finite bins) and stable at 4.986 Hz. The initial
0.5 m / 0.5 rad / 0.5 s scan acceptance thresholds were therefore too coarse
for this compact low-speed course; they were reduced to 0.1 m / 0.1 rad / 0.2 s
for a bounded retest. The pre-tuning bag and map remain evidence, not a PASS.

With the denser scan acceptance settings, the final flat-floor course produced
an 88x139 map with coherent major wall structure and substantially less radial
duplication. Its Robot bag is
`~/maps/issue29/floor-course-slam-tuned-valid-20260824` (MCAP SHA-256
`a6a04b05...2904a`, metadata `4a52a61d...4b19`); the saved YAML is
`88cd5208...9836` and PGM is `a586c38b...a042`. Wheel odometry closed to
0.118 m / 5.3 degrees over 2.30 m, while `map -> base` closed to 0.374 m /
9.3 degrees. The remaining position correction is a short-course accuracy
risk, but no longer constitutes the large map breakage seen before tuning.
The matching Operator control bag MCAP is `6ba31e3b...26b5` and its metadata is
`9353591c...90f4`.

USB reconnect testing exposed a Linux device-lifetime issue: the stable by-id
link returned to event9, but the already-running container retained the old
event handle. Its Joy publisher eventually stopped and teleop correctly timed
out. Recreating the Operator container, pressing PS, and verifying live axes
restored operation. The runbook now makes container recreation mandatory after
every USB reconnect.

For the physical Wi-Fi case, NetworkManager recorded loss at
`1787558715.736` and successful reactivation at `1787558730.178`. The Robot
settled below 0.05 rad/s after 0.721 s. During the 14.44-second outage it still
generated 72 scans and three map updates. The local Operator bag continued to
show command generation for 3.31 seconds after link loss, proving the Robot's
independent controller timeout stopped it. No nonzero command resumed for 181
seconds after reconnection; subsequent movement correlated with new L1 input.

The stationary full-stack soak recorded 279,110 messages over 1798.5 seconds
in `~/maps/issue29/soak-20260824/robot-topics`: metadata SHA-256
`23bef2c0...0b06`, MCAP `cf61eb4a...2f19`. Hesai RSS was 145.3 MiB at both
ends (145.4 MiB maximum), SLAM 78.4 MiB at both ends (78.6 MiB maximum), and
ros2_control rose from 68.1 to 79.5 MiB (79.6 MiB maximum). Final temperature
was 50.15 C, swap was unused, and 14 GiB remained available. The Operator
container remained running with zero restarts/OOM and a final 229 MiB RSS
snapshot. Its periodic stats logger produced no samples, and host networking
makes Docker NetIO unavailable; Operator CPU/memory/network trends therefore
remain an evidence gap. The final software-rendered RViz snapshot used 216%
CPU and reinforces the separate RViz/OpenGL risk in #53.

## Remaining acceptance work

- [x] Validate the wheel-inertia correction removes RViz RobotModel warnings.
- [ ] Resolve and retest the OccupancyGrid display failure in #53.
- [x] Physically operate L1 and each axis, then measure L1/USB disconnect stops.
- [x] Perform controlled Operator Wi-Fi interruption; container stop is not a
      substitute for the AP/firewall/network-path acceptance case.
- [x] Run the repeatable floor course, map-quality review, and map save/reload.
- [x] Complete the 30-60 minute Robot integration soak and resource measurements.

After these gates pass, continue at R01 in
`docs/sanehal2_system_integration.md`. Do not mark hardware cases PASS from the
earlier Issue #27/#41 runs; Issue #29 needs evidence from the distributed
Robot/Operator configuration described by this runbook.
