# 2D Upper-Body Tracking

Code copied verbatim from [the GitBook chapter](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/upper-body-tracking). See that chapter for setup, data formats and limitations.

## Upper-body joints, angles and detection metadata (Network)

Source: [upper_body/01_relative_joints.py](../../examples/documentation/upper_body/01_relative_joints.py)

```bash
python examples/documentation/upper_body/01_relative_joints.py
```

```python
from asmagic import BodyPoseDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def main():
    sub = BodyPoseDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive()
            print("Time:", frame.timestamp)
            print("Upper body:", frame.upper_body)
            print("Detection FPS:", frame.detection_fps)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## Upper-body joints, angles and detection metadata (USB)

Source: [upper_body/01_relative_joints_usb.py](../../examples/documentation/upper_body/01_relative_joints_usb.py)

```bash
python examples/documentation/upper_body/01_relative_joints_usb.py
```

```python
from asmagic import BodyPoseDataSubscriber

IPHONE_IP = "usb"  # Use usb:DEVICE_UDID to select a specific iPhone.


def main():
    sub = BodyPoseDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive()
            print("Time:", frame.timestamp)
            print("Upper body:", frame.upper_body)
            print("Detection FPS:", frame.detection_fps)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```
