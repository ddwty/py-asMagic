# Upper Body Receiving Examples

2D upper-body joints and angles.

[All examples](index.md) · [Data format and API](api-reference.md)

Replace `IPHONE_IP` with your iPhone's IP and start the matching App output. For Watch, enter your computer's IP on Watch. Ctrl-C stops receiving.

## Example 1: Upper-body joints, angles and detection metadata

The upper_body message contains neck, relative arm joints and angles. It is None when absent.

Source: [upper_body/01_relative_joints.py](../../examples/documentation/upper_body/01_relative_joints.py)

Run from the SDK project directory:

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

## Example 2: Enable or disable the upper-body skeleton

Display the received frame. Close the window or press Ctrl-C to finish.

Source: [upper_body/02_optional_skeleton.py](../../examples/documentation/upper_body/02_optional_skeleton.py)

Run from the SDK project directory:

```bash
python examples/documentation/upper_body/02_optional_skeleton.py
```

```python
from asmagic import TrackingPlotter
from asmagic import BodyPoseDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.
SHOW_SKELETON = True


def main():
    sub = BodyPoseDataSubscriber(IPHONE_IP)
    viewer = TrackingPlotter() if SHOW_SKELETON else None
    try:
        while True:
            frame = sub.receive()
            if viewer is not None:
                if not viewer.is_open:
                    break
                viewer.update(frame)
            print("Time:", frame.timestamp)
            print("Upper body:", frame.upper_body)
    except KeyboardInterrupt:
        pass
    finally:
        if viewer is not None:
            viewer.close()
        sub.close()


if __name__ == "__main__":
    main()
```
