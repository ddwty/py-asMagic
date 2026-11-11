# Joystick Receiving Examples

On-screen sticks and buttons, or a connected game controller.

[All examples](index.md) · [Data format and API](api-reference.md)

Replace `IPHONE_IP` with your iPhone's IP and start the matching App output. For Watch, enter your computer's IP on Watch. Ctrl-C stops receiving.

## Example 1: Read named controller controls

Receive one frame and read sticks and named buttons.

Source: [joystick/03_named_controls.py](../../examples/documentation/joystick/03_named_controls.py)

Run from the SDK project directory:

```bash
python examples/documentation/joystick/03_named_controls.py
```

```python
from asmagic import JoystickDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def main():
    sub = JoystickDataSubscriber(IPHONE_IP)
    try:
        while True:
            data = sub.receive()
            print("Time:", data.timestamp)
            print("Left joystick:", data.left_x, data.left_y)
            print("Right joystick:", data.right_x, data.right_y)
            if data.button.square:
                print("Square held")
            print("L1/R1:", data.button.l1, data.button.r1)
            print("L2/R2:", data.button.l2, data.button.r2)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## Example 2: All named controller data

Sticks, named buttons, analog triggers, status and motion.

Source: [joystick/02_full_controller.py](../../examples/documentation/joystick/02_full_controller.py)

Run from the SDK project directory:

```bash
python examples/documentation/joystick/02_full_controller.py
```

```python
from asmagic import JoystickDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def main():
    sub = JoystickDataSubscriber(IPHONE_IP)
    try:
        while True:
            data = sub.receive()
            print("Time:", data.timestamp)
            print("Left joystick:", data.left_x, data.left_y)
            print("Right joystick:", data.right_x, data.right_y)
            print("Triangle:", data.button.triangle)
            print("Square:", data.button.square)
            print("Cross:", data.button.cross)
            print("Circle:", data.button.circle)
            print("L1/R1:", data.button.l1, data.button.r1)
            print("L2/R2:", data.button.l2, data.button.r2)
            print("L3/R3:", data.button.l3, data.button.r3)
            print("D-pad up/down:", data.button.up, data.button.down)
            print("D-pad left/right:", data.button.left, data.button.right)
            print("Share/Options:", data.button.share, data.button.options)
            print("Home/Touchpad:", data.button.home, data.button.touchpad)
            print("Controller:", data.controller_name)
            print("Connected:", data.is_connected)
            print("Battery:", data.battery_level)
            print("Charging:", data.is_charging)
            if data.has_motion:
                print("Gravity (G):", data.gravity)
                print("Acceleration (G):", data.user_acceleration)
                print("Rotation rate (rad/s):", data.rotation_rate)
                print("Attitude:", data.attitude)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## Example 3: Old API: sticks and numbered buttons

Existing numbered button fields remain supported.

Source: [joystick/01_sticks_and_buttons.py](../../examples/documentation/joystick/01_sticks_and_buttons.py)

Run from the SDK project directory:

```bash
python examples/documentation/joystick/01_sticks_and_buttons.py
```

```python
from asmagic import JoystickDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def main():
    sub = JoystickDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive()
            print("Time:", frame.timestamp)
            print("Left joystick:", frame.left_x, frame.left_y)
            print("Right joystick:", frame.right_x, frame.right_y)
            print("Triangle:", frame.button1)
            print("Square:", frame.button2)
            print("Cross:", frame.button3)
            print("Circle:", frame.button4)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```
