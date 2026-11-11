# AirPods Receiving Examples

AirPods head rotation.

[All examples](index.md) · [Data format and API](api-reference.md)

Replace `IPHONE_IP` with your iPhone's IP and start the matching App output. For Watch, enter your computer's IP on Watch. Ctrl-C stops receiving.

## Example 1: AirPods rotation quaternion

Rotation is a quaternion in x/y/z/w order.

Source: [airpods/01_rotation.py](../../examples/documentation/airpods/01_rotation.py)

Run from the SDK project directory:

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
