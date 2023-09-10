# sanehal_behicle_description

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

```
flowchart LR
    main[diffbot.urdf.xacro]
    system(diffbot_system.urdf.xacro)
    description(diffbot_description.urdf.xacro)
    materials(diffbot.materials.xacro)
    ros2_control(diffbot.ros2_control.xacro)
    gazebo(gazeobo/diffbot.gazebo.xacro)
    gazebo_materials(gazebo/diffbot.materials.xacro)

    main---ros2_control
    main---description
    main---materials
    
    system---main
    system---gazebo_materials
    system---gazebo
```