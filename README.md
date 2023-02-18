# Project SANEHAL

## 事前準備

- ROSのインストール
- Dynamixelのrulesファイル追加とデバイス再起動
- ldlidarのrulesファイル追加とデバイス再起動


## ビルド方法
```bash
mkdir -p ws_sanehal/src
cd ws_sanehal/src
git clone git@github.com:MrBearing/sanehal.git
cd sanehal/
git switch issue_apply_ros2_control # 任意
vcs import src < src/sanehal/sanehal.repos
rosdep install -i --from-paths src
sudo apt install -y ros-humble-xacro　#ros-depで入らなかった場合の対応
colcon build --symlink-install
```

## 動作確認
```bash
. install/setup.bash
ros2 launch sanehal_vehicle_description diffbot_pi.launch.py # pi上で
ros2 launch sanehal_vehicle_description diffbot.launch.py # 母艦PC上で
```