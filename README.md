# Project SANEHAL

[![ci_jazzy](https://github.com/MrBearing/sanehal/actions/workflows/ci_jazzy.yaml/badge.svg)](https://github.com/MrBearing/sanehal/actions/workflows/ci_jazzy.yaml)
[![ci_lyrical](https://github.com/MrBearing/sanehal/actions/workflows/ci_lyrical.yaml/badge.svg)](https://github.com/MrBearing/sanehal/actions/workflows/ci_lyrical.yaml)

## 事前準備

### ワークスペース作成とリポジトリのクローン

```bash
mkdir -p ws_sanehal/src
cd ws_sanehal/src
git clone git@github.com:MrBearing/sanehal.git
cd sanehal/
./setup.bash
```
### ROSのインストール

[ここを](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html#install-ros-2)参照

### ldlidarとDynamixelのrulesファイル追加とデバイス再起動

```bash
# src/sanehal下で
cp dev_rules/*.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

[参考](http://linux-tips.org/t/prevent-modem-manager-to-capture-usb-serial-devices/284/2)

## ビルド方法
```bash
colcon build
```

## 動作確認
```bash
. install/setup.bash
ros2 launch sanehal_vehicle_description diffbot_pi.launch.py # pi上で
ros2 launch sanehal_vehicle_description diffbot.launch.py # 母艦PC上で
```