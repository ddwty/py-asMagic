# AirPods Motion

Code copied verbatim from [the GitBook chapter](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/airpods-and-gripper). See that chapter for setup, data formats and limitations.

## AirPods rotation quaternion (Network)

Source: [airpods/01_rotation.py](../../examples/documentation/airpods/01_rotation.py)

```bash
python examples/documentation/airpods/01_rotation.py
```

```python
from asmagic import AirPodsDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def main():
    sub = AirPodsDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive()
            print("Time:", frame.timestamp)
            print("Rotation:", frame.rotation)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## AirPods rotation quaternion (USB)

Source: [airpods/01_rotation_usb.py](../../examples/documentation/airpods/01_rotation_usb.py)

```bash
python examples/documentation/airpods/01_rotation_usb.py
```

```python
from asmagic import AirPodsDataSubscriber

IPHONE_IP = "usb"  # Use usb:DEVICE_UDID to select a specific iPhone.


def main():
    sub = AirPodsDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive()
            print("Time:", frame.timestamp)
            print("Rotation:", frame.rotation)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```
