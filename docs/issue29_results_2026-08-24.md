# Issue #29 integration result — 2026-08-24

Status: **IN PROGRESS — raised-wheel teleoperation passed; floor/network/soak remain**

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

## Remaining acceptance work

- [x] Validate the wheel-inertia correction removes RViz RobotModel warnings.
- [ ] Resolve and retest the OccupancyGrid display failure in #53.
- [x] Physically operate L1 and each axis, then measure L1/USB disconnect stops.
- [ ] Perform controlled Operator Wi-Fi interruption; container stop is not a
      substitute for the AP/firewall/network-path acceptance case.
- [ ] Run the repeatable floor course, map-quality review, and map save/reload.
- [ ] Complete the 30-60 minute integration soak and resource measurements.

After these gates pass, continue at R01 in
`docs/sanehal2_system_integration.md`. Do not mark hardware cases PASS from the
earlier Issue #27/#41 runs; Issue #29 needs evidence from the distributed
Robot/Operator configuration described by this runbook.
