台車部分コントロール用のパッケージ

ビルドにはDynamixelSDKとdynamixel-workbench,そしてdynamixel-hardwareが必要です。


ros2_controlを使用して実装します。


## 実行方法

表示テスト

```bash
ros2 launch sanehal_vehicle_bringup diffbot.launch.py
```


```
ros2 launch sanehal_vehicle_description diffbot.launch.py
```

```
ros2 topic pub --rate 30 /diffbot_base_controller/cmd_vel_unstamped geometry_msgs/msg/Twist "linear:
    x: 0.3
    y: 0.0
    z: 0.0
angular:
    x: 0.0
    y: 0.0
    z: 1.0"
```


## run only

```
ros2 topic pub --rate 30 /cmd_vel geometry_msgs/msg/Twist "linear:
    x: 0.7
    y: 0.0
    z: 0.0
angular:
    x: 0.0
    y: 0.0
    z: 1.0"

```