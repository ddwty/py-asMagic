# asMagic Python SDK

[![Tests](https://github.com/ddwty/py-asMagic/actions/workflows/ci.yml/badge.svg)](https://github.com/ddwty/py-asMagic/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/asmagic.svg)](https://pypi.org/project/asmagic/)
[![Python](https://img.shields.io/pypi/pyversions/asmagic.svg)](https://pypi.org/project/asmagic/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Receive camera images, depth, device motion, controller input, body joints, hands and face tracking from the [asMagic iPhone app](https://apps.apple.com/app/id6661033548).

[中文](README.zh-CN.md) · [Examples](docs/examples/index.md) · [API reference](docs/api.md) · [Wire protocol](docs/protocols.md)

## Installation

Requires Python 3.8 or newer.

```bash
python -m pip install asmagic
```

The default installation includes image decoding with Pillow, OpenCV and PyAV, and plotting with Matplotlib. Generated Protobuf bindings ship with the package; `protoc` is only needed when changing schemas.

## Quick start

1. Connect the iPhone and computer to the same reachable network.
2. Open **Stream → Camera** in asMagic, choose a lens and enable **Stream Video**. Allow local-network access when prompted.
3. Replace the address below with the **iPhone's IP address** and run the script.

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

`color_array` is an RGB NumPy array. HEVC streams may need a keyframe before an image becomes available. To display the video, run [camera_only.py](examples/camera_only.py) after editing its `IPHONE_IP`.

Each app feature starts its own output. Open the corresponding feature and enable sending before using another receiver. Python receivers connect directly to the iPhone; pairing with the Mac app is unnecessary.

## Available streams

Import receivers directly from `asmagic`. All ZeroMQ ports below use TCP.

| Data | Receiver | Default port | Guide |
|---|---|---:|---|
| Camera RGB and capture metadata | `CameraDataSubscriber` | 8105 | [Camera](docs/examples/camera.md) |
| AR RGB, depth, confidence, camera pose and intrinsics | `ARDataSubscriber` | 8000 | [AR](docs/examples/ar.md) |
| iPhone motion sensors | `IMUDataSubscriber` | 8002 | [IMU](docs/examples/imu.md) |
| Controller buttons, sticks and triggers | `JoystickDataSubscriber` | 8020 | [Controller](docs/examples/joystick.md) |
| ARKit body joints | `BodyTrackingDataSubscriber(model="arkit")` | 8100 | [Body](docs/examples/body.md) |
| MediaPipe people and landmarks | `BodyTrackingDataSubscriber(model="mediapipe")` | 8104 | [Body](docs/examples/body.md) |
| Hand joints | `HandPoseDataSubscriber` | 8101 | [Hands](docs/examples/hand.md) |
| Face landmarks, mesh and blendshapes | `FaceDataSubscriber` | 8102 | [Face](docs/examples/face.md) |
| Vision 2D upper-body joints | `BodyPoseDataSubscriber` | 8010 | [Upper body](docs/examples/upper_body.md) |
| AirPods head orientation | `AirPodsDataSubscriber` | 8001 | [AirPods](docs/examples/airpods.md) |
| Gripper commands | `ClawDataSubscriber` | 5301 / 5401 | [Gripper](docs/examples/claw.md) |
| Apple Watch motion batches | `WatchIMUReceiver` | HTTP 8002 | [Watch](docs/examples/watch.md) |

**Watch uses the opposite connection direction:** Python starts an HTTP receiver, and the Watch sends to the **computer's IP address**. See the Watch guide for binding and device configuration.

## Receiving data

Receivers support context managers, iteration and explicit timeouts. `receive()` waits for a valid frame; `receive(timeout=1000)` waits up to 1,000 milliseconds and returns `None` on timeout. Closing a receiver ends iteration and makes `receive()` raise `StopIteration`.

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

Read every field you need from the same frame. Calling `receive()` again advances to another frame. `frame.protobuf` exposes the original decoded message; receivers also support offline decoding of saved payloads.

Body and hand APIs provide named joints and NumPy skeleton arrays. Face and hand outputs are independent. Tracking availability, coordinate spaces, units and device capabilities are documented in the [API reference](docs/api.md) and [protocol guide](docs/protocols.md).

## Examples and diagnostics

Clone the repository to run the complete examples:

```bash
git clone https://github.com/ddwty/py-asMagic.git
cd py-asMagic
python -m pip install -e .
python examples/documentation/hand/01_both_hands.py
```

Edit each script's `IPHONE_IP` first. Tracking examples offer a `SHOW_SKELETON` switch. The [example index](docs/examples/index.md) covers all streams, plotting, saving messages and offline decoding.

For a guided device check:

```bash
asmagic-test --list
asmagic-test hand --ip 192.168.1.100 --plot
```

If no data arrives, check the selected app feature, its output toggle, the sender address and firewall settings. `is_connected` indicates an open local receiver; `received_frames` counts actual received frames. ZeroMQ PUB/SUB is best effort, and some receivers keep only the newest frame by default. Use a trusted local network: these stream transports do not provide authentication or encryption.

## Development

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
python tools/sync_documentation_examples.py --check
python tools/check_repository.py
python -m build
python -m twine check dist/*
```

Tests use synthetic fixtures and local TCP/HTTP connections. Device recognition quality and sustained wireless delivery require checks with the actual iPhone or Watch. See [CONTRIBUTING.md](CONTRIBUTING.md) for the development workflow and [upgrade notes](docs/compatibility.md) for older APIs.

## License

[MIT](LICENSE). This license covers the Python SDK in this repository. The companion app is distributed separately.
