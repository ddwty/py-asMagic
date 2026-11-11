# 逐个测试 App 数据流与绘图

运行单个数据流可使用[独立示例](examples/index.md) 和 [文件清单](../examples/documentation/README.md)。每段代码与对应 `.py` 文件逐字一致，包含完整导入、IP、接收循环和清理逻辑，以及可选的骨架显示开关。本页的工具适用于需要逐项引导与报告的情况。

## 文件位置

| 位置 | 用途 |
|---|---|
| `examples/test_app_streams.py` | 连接真实 App 的统一测试入口；支持单项、逐项引导、绘图和 JSON 报告 |
| `examples/read_body_data.py` | 三维全身骨架接收示例；`--plot` 开启绘图 |
| `examples/read_upper_body_data.py` | 二维上半身接收示例；`--plot` 开启绘图 |
| `examples/read_hand_data.py` | 双手接收示例；`--plot` 开启绘图 |
| `examples/read_face_data.py` | 独立面部接收示例；`--plot` 开启绘图 |
| `examples/read_face_hand_data.py` | 选择面部或手部；同时接收时在两个终端分别运行 |
| `examples/preview_tracking_plots.py` | 无需设备，导出明确标记为合成数据的人体/双手 PNG 预览 |
| `tests/` | SDK 自动回归测试，使用合成数据与本机 TCP/HTTP，不会测试真实 App 的识别效果 |
| `asmagic/plotting.py` | API 绘图实现；Matplotlib 随 SDK 默认安装 |
| `asmagic/diagnostics.py`、`asmagic/cli.py` | 字段检查、有限时长接收、逐项测试与报告实现 |

## 安装

在含有 `pyproject.toml` 的 `asmagic/` 项目目录执行：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Windows 激活命令为 `.venv\Scripts\activate`。默认安装包含全部运行依赖，包括 Matplotlib 与相机 HEVC 解码的 PyAV，无需额外选择安装项。关闭绘图不导入 Matplotlib、不创建窗口。绘图窗口需要桌面环境，macOS 请在主线程使用。

## 按顺序测试全部数据流

```bash
python examples/test_app_streams.py --list
python examples/test_app_streams.py --all --ip 192.168.1.100 --plot --images
```

也可以使用安装后提供的 `asmagic-test --all --ip 192.168.1.100 --plot --images`。

`--ip` 填发送 iPhone 的地址。程序按步骤提示 App 操作：Enter 开始接收，`s` 跳过没有硬件或暂时不测的通道，`q` 结束。每项默认接收 15 秒，可用 `--duration 30` 调整。由于相机、人体、前置面部可能占用不同会话，每个步骤只打开对应功能并开始发送。不要在后台同时打开全部接收器后等待所有端口都出数据。

| 测试名称 | 默认端口 | App 操作与检查目标 |
|---|---:|---|
| `camera` | 8105 TCP | Stream → Camera → Send camera，切换前后置镜头，检查 RGB 图像 |
| `ar` | 8000 TCP | Stream；移动手机，检查相机、深度、位姿、内参；Robot control 位姿也用此通道 |
| `airpods` | 8001 TCP | AirPods 头部跟踪；转动头部，检查姿态四元数 |
| `imu` | 8002 TCP | iPhone IMU；转动/移动手机，检查传感器向量 |
| `body_pose` | 8010 TCP | 二维上半身；抬手，检查肩、肘、手腕 |
| `joystick` | 8020 TCP | 手柄或虚拟摇杆；操作双摇杆、按钮与扳机 |
| `ar_body` | 8100 TCP | Body tracking；全身进入画面，走动、抬手、屈膝 |
| `hand` | 8101 TCP | Stream 开启手部发送，或 Face and Hand Tracking → Hand tracking → Send hands；两个入口使用同一接收代码，双手进入画面、移动手指 |
| `face` | 8102 TCP | Face and Hand Tracking → Face tracking → Send face；张嘴、眨眼；与手部独立 |
| `claw` | 5301 TCP | 第一个夹爪的数据输出；检查命令与可选 motor 信息 |
| `claw2` | 5401 TCP | 第二个夹爪；没有此功能时跳过 |
| `watch` | 8002 HTTP | Python 监听；Watch 配置计算机 IP/端口，移动手腕 |

Watch 与 iPhone IMU 的 8002 使用不同传输方向。Watch 步骤会先启动本机 HTTP 服务，请在 Watch 填写这台计算机的局域网 IP，不能填 `0.0.0.0` 或 iPhone IP。用 `--watch-port` 调整全量测试中的 Watch 端口。

## 单项测试

```bash
python examples/test_app_streams.py ar_body --ip 192.168.1.100 --plot
python examples/test_app_streams.py hand --ip 192.168.1.100 --plot
python examples/test_app_streams.py face --ip 192.168.1.100 --plot
python examples/test_app_streams.py body_pose --ip 192.168.1.100 --plot
python examples/test_app_streams.py ar --ip 192.168.1.100 --images
python examples/test_app_streams.py watch --bind 0.0.0.0 --port 8002
```

其他通道替换测试名称即可。`--port` 覆盖单项端口；`--count 100` 收到 100 帧后提前结束。绘图默认关闭；`--plot` 只绘制跟踪通道，`--images` 只显示相机图像。关闭跟踪窗口结束当前项目；Ctrl-C 结束接收并保存当前报告。世界坐标绘图使用 `--space world`；不存在 `body_transform` 的帧会显示为空，不会偷偷改用人体坐标。

## 结果与报告

程序显示收到的帧数、有效结果帧数、实际接收速率和当前字段。它检查向量长度/有限数值、位姿、图像解码/深度尺寸、手部置信度、人体变换和 Watch 样本。默认报告保存在 `reports/app-streams.json`，可用 `--report 路径` 指定。每个步骤后即保存，提前退出的项目标记为 `not_run`，没有硬件而跳过的标记为 `skipped`。

| 状态 | 含义 |
|---|---|
| `received` | 收到有效字段，已执行检查未发现错误 |
| `received_with_errors` | 有有效数据，也出现过解码或字段错误 |
| `empty_data` | 收到帧，但没有实际传感器/跟踪结果，例如只有寻找人体的状态 |
| `no_data` | 在指定时长内未收到帧；打开 socket 不算收到数据 |
| `errors` | 接收或字段检查出现错误 |
| `skipped` / `not_run` | 人工跳过 / 尚未执行 |

`component_frames` 记录各字段出现次数，`last_values` 为最后一帧摘要，Watch 分开记录批次与样本数。引导模式还会询问动作与数值/绘图是否对应，记录为 `matches`、`does_not_match` 或 `not_checked`。收到 Protobuf 并不证明识别准确；请看图并实际完成动作。缺失的可选字段可能由设备能力或功能配置决定，例如 Vision 面部没有 TrueDepth 的 52 系数和米制网格。

## API 中开启或关闭绘图

使用 `SHOW_SKELETON = True/False` 选择是否显示骨架：

```python
from asmagic import BodyTrackingDataSubscriber, TrackingPlotter

IPHONE_IP = "192.168.1.100"
MODEL = "mediapipe"  # Match the App setting: "mediapipe" or "arkit".
SHOW_SKELETON = True


def main():
    sub = BodyTrackingDataSubscriber(IPHONE_IP, model=MODEL)
    plotter = None
    try:
        plotter = TrackingPlotter(space="body", min_confidence=0.5) if SHOW_SKELETON else None
        while plotter is None or plotter.is_open:
            frame = sub.receive(timeout=50 if plotter is not None else 1000)
            if frame is None:
                if plotter is not None:
                    plotter.idle()
                continue
            print("People:", frame.person_count, "IDs:", [person.id for person in frame.people])
            if plotter is not None:
                plotter.update(frame)
    except (KeyboardInterrupt, StopIteration):
        pass
    finally:
        sub.close()
        if plotter is not None:
            plotter.close()


if __name__ == "__main__":
    main()
```

手部、面部和上半身使用同样的接收结构。用 `TrackingPlotter.update(frame)` 显示收到的数据：

```python
from asmagic import HandPoseDataSubscriber, HandTrackingWindow

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.
SHOW_SKELETON = True


def main():
    sub = HandPoseDataSubscriber(IPHONE_IP)
    viewer = None
    try:
        viewer = HandTrackingWindow(labels=True, min_confidence=0.5) if SHOW_SKELETON else None
        while True:
            frame = sub.receive(timeout=50)
            if viewer is not None:
                if not viewer.is_open:
                    break
                viewer.update(frame)
            if frame is None:
                continue
            print("Time:", frame.timestamp)
            print("Left hand detected:", frame.left is not None)
            print("Right hand detected:", frame.right is not None)
    except (KeyboardInterrupt, StopIteration):
        pass
    finally:
        if viewer is not None:
            viewer.close()
        sub.close()


if __name__ == "__main__":
    main()
```

单帧也提供 `frame.plot(enabled=True)`、`hand.plot(enabled=True)`。返回可复用的 `TrackingPlotter`；用 `frame.plot(plotter=viewer)` 更新已有窗口，结束后 `viewer.close()`。`enabled=False` 返回 `None`。保存当前图像使用 `viewer.save("body.png", dpi=150)`；无桌面环境可在导入绘图前选择 Matplotlib 的 `Agg` 后端后保存文件。

人体使用三维米制坐标和实际 `joint_parents` 连线；直接跟踪与估算/无标记节点采用不同颜色。双手采用原始图像归一化坐标，左上角原点，分别标明人的左手和右手；只连接两端都存在的骨段。二维上半身把相对向量累加到颈部坐标，存在 `json_data.detected_joints` 时隐藏发送端补齐的历史/默认节点。没有这份元数据时图中明确标注检测标记不可用。

绘图不会改变收到的数据、旋转或镜像坐标，也不会改变 App 的发送帧率。`TrackingPlotter(max_fps=30, labels=False, stale_after=2)` 控制绘制频率、关节标签和停止接收后的清空时长。调用 `idle()` 可处理无数据时的窗口事件和清空旧骨架。父关节坐标各有不同原点，绘图不接受 `PARENT` 空间；数组 API 仍支持它。

## SDK 自动回归测试

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
```

`tests/test_plotting.py` 检查绘图坐标、真实骨段、缺失与停发清空、开关和窗口复用；`tests/test_device_checks.py` 检查测试清单、有限时长接收、无数据/空数据/错误的区分、报告格式。其他测试继续验证协议、旧接口、本机 TCP/HTTP、图像与关节数组。这些自动测试使用合成输入，不代替真实 App 测试。

先查看绘图样式而不连接设备，可运行 `python examples/preview_tracking_plots.py`。输出 `reports/body-preview.png` 和 `reports/hands-preview.png`；图中已注明是合成夹具，不能用它们判断 App 的识别效果。
