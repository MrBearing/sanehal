# Project SANEHAL

[![ci_jazzy](https://github.com/MrBearing/sanehal/actions/workflows/ci_jazzy.yaml/badge.svg)](https://github.com/MrBearing/sanehal/actions/workflows/ci_jazzy.yaml)

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

## SLAM機能

### SLAMでマップ作成
```bash
# ワークスペースのセットアップ
. install/setup.bash

# SLAMを起動（ロボット、LiDAR、slam_toolbox、RVizが同時に起動）
ros2 launch sanehal_bringup slam.launch.py

# ロボットを動かしてマップを作成
# 別ターミナルでキーボードテレオプを起動（必要に応じて）
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# マップが完成したら、別ターミナルでマップを保存
ros2 launch sanehal_bringup save_map.launch.py map_name:=my_office_map
```

### 作成されるファイル
- `my_office_map.pgm` - マップ画像ファイル
- `my_office_map.yaml` - マップメタデータファイル

### パラメータ調整
SLAM動作のパラメータは `sanehal_bringup/config/slam_toolbox_params.yaml` で調整できます。