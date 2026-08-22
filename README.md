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

### JT16とDynamixelのrulesファイル追加とデバイス再起動

```bash
# src/sanehal下で
sudo usermod -aG dialout "$USER"
sudo cp dev_rules/*.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
ls -l /dev/jt16_rs485 /dev/jt16_rs232 /dev/dxhub
```

JT16の2つのUSB-serial adapterは`dev_rules/99-jt16.rules`に記録された
vendor/product/serial番号で識別されます。別のadapterへ交換した場合は、
`udevadm info --attribute-walk --name=/dev/ttyUSB0`等で実機の属性を確認して
ruleを更新してください。実行ユーザーは`dialout` groupに所属している必要があります。
group追加後はログアウトして再ログインしてください。

[参考](http://linux-tips.org/t/prevent-modem-manager-to-capture-usb-serial-devices/284/2)

## ビルド方法
```bash
colcon build
```

## 動作確認
```bash
. install/setup.bash
ros2 launch sanehal_bringup jt16.launch.py       # JT16 driverのみ
ros2 launch sanehal_bringup sanehal.launch.py    # Raspberry Pi上のRobot + JT16 + 2D SLAM
ros2 launch sanehal_operator operator.launch.py  # Operator環境上での表示のみ
```

Robot bringupはRVizを起動しません。Ubuntu 26.04 Operator PCでは、ROS 2
JazzyをUbuntu 24.04 container内で実行します。VS Codeを使わない通常起動は
次の通りです。詳細は `sanehal_operator/README.md` を参照してください。

```bash
ROS_DOMAIN_ID=42 scripts/operator/configure.sh  # 配備ごとに値を選ぶ
scripts/operator/up.sh
```

For USB PlayStation gamepad teleoperation, identify its stable
`/dev/input/by-id/*-event-joystick` link and pass it during configuration:

```bash
ROS_DOMAIN_ID=42 \
GAMEPAD_BY_ID=/dev/input/by-id/<controller>-event-joystick \
GAMEPAD_MODEL=DualSense \
scripts/operator/configure.sh
scripts/operator/up.sh
```

See `sanehal_operator/README.md` for the mandatory mapping and raised-wheel
safety tests. Bluetooth is not used; the controller connects to the host with a
USB data cable.

RobotとOperator PCで同じ`ROS_DOMAIN_ID`、`rmw_fastrtps_cpp`、discovery
設定を使用してください。実機なしのgraph/TF確認には次を使用できます。

```bash
ros2 launch sanehal_bringup sanehal.launch.py use_mock_hardware:=true \
  start_lidar:=false start_pointcloud_to_laserscan:=false start_slam:=false
```
