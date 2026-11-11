# Gripper Receiving Examples

Gripper commands and reported motor state.

[All examples](index.md) · [Data format and API](api-reference.md)

Replace `IPHONE_IP` with your iPhone's IP and start the matching App output. For Watch, enter your computer's IP on Watch. Ctrl-C stops receiving.

## Example 1: First gripper command and optional motor state

angle is the App percent command. Optional motor state is printed as received.

Source: [claw/01_first_gripper.py](../../examples/documentation/claw/01_first_gripper.py)

Run from the SDK project directory:

```bash
python examples/documentation/claw/01_first_gripper.py
```

```python
from asmagic import ClawDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def main():
    sub = ClawDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive()
            print("Time:", frame.timestamp)
            print("Gripper command (%):", frame.angle)
            print("Motor:", frame.motor)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## Example 2: Second gripper on a separate port

The second gripper uses port 5401.

Source: [claw/02_second_gripper.py](../../examples/documentation/claw/02_second_gripper.py)

Run from the SDK project directory:

```bash
python examples/documentation/claw/02_second_gripper.py
```

```python
from asmagic import ClawDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def main():
    sub = ClawDataSubscriber(IPHONE_IP, port=5401)
    try:
        while True:
            frame = sub.receive()
            print("Time:", frame.timestamp)
            print("Gripper command (%):", frame.angle)
            print("Motor:", frame.motor)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```
