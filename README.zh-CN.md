# asMagic Python SDK

通过 Python 接收 [asMagic iPhone App](https://apps.apple.com/app/id6661033548) 的相机图像、深度、设备运动、手柄输入、人体关节、手部和面部跟踪数据。

[English](README.md) · [完整示例](docs/examples/index.md) · [API 参考](docs/api.md) · [协议与端口](docs/protocols.md)

## 安装

需要 Python 3.8 或更新版本，建议在虚拟环境中安装。

```bash
python -m pip install asmagic
```

默认安装包含 Pillow、OpenCV、PyAV 图像解码和 Matplotlib 绘图依赖。包中已包含生成的 Protobuf 绑定，使用 SDK 不需要安装 `protoc`。

## 快速开始

1. 将 iPhone 与计算机连接到可以互相访问的网络。
2. 在 asMagic 中打开 **Stream → Camera**，选择镜头并开启 **Stream Video**；按系统提示允许访问本地网络。
3. 将以下地址改为 **iPhone 的 IP**，运行脚本。

```python
from asmagic import CameraDataSubscriber

IPHONE_IP = "192.168.1.100"

try:
    with CameraDataSubscriber(IPHONE_IP) as camera:
        for frame in camera:
            rgb = frame.color_array
            if rgb is not None:
                print(frame.timestamp, rgb.shape)
except KeyboardInterrupt:
    pass
```

`color_array` 为 RGB NumPy 数组。刚连接 HEVC 视频时，可能需要等待关键帧才能获得图像。修改 [camera_only.py](examples/camera_only.py) 中的 `IPHONE_IP` 后运行，即可预览视频。

不同功能需要分别开启对应输出，打开某个页面不会启用所有端口。Python 直接连接 iPhone，无需先与 Mac App 配对。

## 数据流

以下接收类均从 `asmagic` 导入；ZeroMQ 使用 TCP。

| 数据 | 接收类 | 默认端口 | 示例 |
|---|---|---:|---|
| 普通相机 RGB 和采集元数据 | `CameraDataSubscriber` | 8105 | [Camera](docs/examples/camera.md) |
| AR 图像、深度、置信度、位姿和内参 | `ARDataSubscriber` | 8000 | [AR](docs/examples/ar.md) |
| iPhone 运动传感器 | `IMUDataSubscriber` | 8002 | [IMU](docs/examples/imu.md) |
| 手柄按键、摇杆和扳机 | `JoystickDataSubscriber` | 8020 | [手柄](docs/examples/joystick.md) |
| ARKit 人体关节 | `BodyTrackingDataSubscriber(model="arkit")` | 8100 | [人体](docs/examples/body.md) |
| MediaPipe 多人关节 | `BodyTrackingDataSubscriber(model="mediapipe")` | 8104 | [人体](docs/examples/body.md) |
| 手部关节 | `HandPoseDataSubscriber` | 8101 | [手部](docs/examples/hand.md) |
| 面部特征点、网格和表情系数 | `FaceDataSubscriber` | 8102 | [面部](docs/examples/face.md) |
| Vision 二维上半身 | `BodyPoseDataSubscriber` | 8010 | [上半身](docs/examples/upper_body.md) |
| AirPods 头部方向 | `AirPodsDataSubscriber` | 8001 | [AirPods](docs/examples/airpods.md) |
| 夹爪指令 | `ClawDataSubscriber` | 5301 / 5401 | [夹爪](docs/examples/claw.md) |
| Apple Watch 运动批次 | `WatchIMUReceiver` | HTTP 8002 | [Watch](docs/examples/watch.md) |

**Watch 的方向相反：** Python 启动 HTTP 接收器，Watch 将数据发往**计算机的 IP**。监听地址和设备配置见 Watch 示例。

## 接收方式

`receive()` 等待一个有效帧；`receive(timeout=1000)` 最多等待 1,000 毫秒，超时返回 `None`。接收器支持 `with` 和迭代，退出时自动释放资源；关闭后 `receive()` 抛出 `StopIteration`。

```python
from asmagic import IMUDataSubscriber

IPHONE_IP = "192.168.1.100"

try:
    with IMUDataSubscriber(IPHONE_IP) as motion:
        while True:
            frame = motion.receive(timeout=1000)
            if frame is not None and frame.has_accelerometer:
                print(frame.accelerometer)
except KeyboardInterrupt:
    pass
```

需要的字段应从同一个 `frame` 读取；再次调用 `receive()` 会进入下一帧。`frame.protobuf` 可访问原始消息，接收类也支持离线解码。

人体和手部提供具名关节与 NumPy 数组接口。面部、手部独立输出；字段缺失、坐标空间、单位及设备能力见 [API 参考](docs/api.md)和[协议说明](docs/protocols.md)。

## 运行示例

```bash
git clone https://github.com/ddwty/py-asMagic.git
cd py-asMagic
python -m pip install -e .
python examples/documentation/hand/01_both_hands.py
```

运行前修改脚本中的 `IPHONE_IP`；跟踪示例通过 `SHOW_SKELETON` 控制绘图。[示例目录](docs/examples/index.md)覆盖全部数据流、图像、骨架、消息保存和离线解码。

逐项检查设备输出：

```bash
asmagic-test --list
asmagic-test hand --ip 192.168.1.100 --plot
```

收不到数据时，检查 App 功能页、发送开关、iPhone 地址和防火墙。`is_connected` 表示本地接收器已打开，`received_frames` 才表示实际接收计数。ZeroMQ PUB/SUB 为尽力传输，部分通道默认只保留最新帧。请在可信局域网中使用：这些传输未提供认证或加密。

## 开发与许可证

开发安装、自动测试与打包流程见 [CONTRIBUTING.md](CONTRIBUTING.md)。测试使用合成夹具及本机 TCP/HTTP；真实识别效果和持续无线传输需要使用 iPhone / Watch 检查。

本仓库 Python SDK 使用 [MIT 许可证](LICENSE)。配套 App 独立分发。
