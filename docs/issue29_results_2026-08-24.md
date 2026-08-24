# Issue #29 integration result — 2026-08-24

Status: **IN PROGRESS — hardware motion gate not yet opened**

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
| Robot source | `jazzy` at base commit; untracked `AGENTS.md` and `test_jt16.bash` | BLOCKED: issue branch not deployed; preserve user files |
| Operator gamepad | USB Sony PLAYSTATION 3, stable by-id link to event9 | PASS |
| Operator domain | 42 | FAIL: differs from Robot login environment |
| Robot domain | 61 in `.bashrc` | FAIL: differs from Operator `.env` |
| Physical safety | raised wheels, exclusion zone, observer, and physical stop not remotely verifiable | BLOCKED |

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

After these gates pass, continue at R01 in
`docs/sanehal2_system_integration.md`. Do not mark hardware cases PASS from the
earlier Issue #27/#41 runs; Issue #29 needs evidence from the distributed
Robot/Operator configuration described by this runbook.
