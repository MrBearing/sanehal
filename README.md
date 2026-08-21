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
ros2 launch sanehal_bringup sanehal.launch.py    # Raspberry Pi上の駆動系 + JT16
ros2 launch sanehal_bringup sanehal_rviz.launch.py # 母艦PC上での表示のみ
```
