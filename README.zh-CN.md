# asMagic Python SDK

通过 Python 接收 [asMagic iPhone App](https://apps.apple.com/app/id6661033548) 的相机、深度、运动传感器、手柄和跟踪数据。

**[使用文档](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data)** · [English](README.md)

## 安装

需要 Python 3.8 或更新版本。

```bash
python -m pip install asmagic
```

## 文档

设备配置、接收示例、数据格式和 API 说明请阅读 [asMagic GitBook 文档](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data)。

从[快速开始](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/quick-start)接收第一帧数据。

## USB 连接

现有接收代码只需将 iPhone IP 换成 `"usb"`：

```python
import asmagic

with asmagic.IMUDataSubscriber("usb") as sub:
    for frame in sub:
        print(frame.accelerometer)
```

运行 `asmagic usb list` 发现有线设备，`asmagic usb setup` 配置新电脑的系统 USB 支持。
[USB 使用说明](docs/USB.md)包含 Mac、Windows、Linux、树莓派及双向通信示例。
需要 SDK 1.1.0+ 和支持 USB 的 iPhone 版本。完整步骤见 [GitBook USB 指南](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/usb-connection)。

## 参与贡献

开发环境和检查流程见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可证

[MIT](LICENSE)。
