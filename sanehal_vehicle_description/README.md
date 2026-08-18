# sanehal_behicle_description

## SANEHAL-2 JT16 frame

JT16のframeは `sanehal_base_link` からfixed joint `jt16_joint` で接続する
`hesai_lidar` です。Issue #30ではHesai driverの `ros.ros_frame_id` を
同じ値にしてください。TFは `robot_state_publisher` が配信するため、driverの
launchから同じstatic TFを重複配信しないでください。

SANEHAL-2で実測した取付TFは `xyz="-0.080 0 0.250"` [m]、`rpy="0 0 0"`
[rad] です。`hesai_lidar` の物理基準はJT16底面中心で、コネクタ面は機体後方を向きます。

visual/collisionは実測外形 `0.075 x 0.075 x 0.064` [m] の簡略boxです。
link原点が底面中心のため、box中心はz方向へ `0.032` [m] offsetしています。

このパッケージは[ros2_control_demos](https://github.com/ros-controls/ros2_control_demos)のdiffbotを改変して作成されました。

## 概要
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


## 構造

```urdf :mermaid
flowchart LR
    main[diffbot.urdf.xacro]
    description(diffbot_description.urdf.xacro)
    materials(diffbot.materials.xacro)
    ros2_control(diffbot.ros2_control.xacro)
    gazebo(gazeobo/diffbot.gazebo.xacro)
    gazebo_materials(gazebo/diffbot.materials.xacro)

    main---ros2_control
    main---description
    main---materials
```