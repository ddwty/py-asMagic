# Joystick

Code copied verbatim from [the GitBook chapter](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/joystick-receiving-example). See that chapter for setup, data formats and limitations.

## Read named controller controls (Network)

Source: [joystick/03_named_controls.py](../../examples/documentation/joystick/03_named_controls.py)

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

## Read named controller controls (USB)

Source: [joystick/03_named_controls_usb.py](../../examples/documentation/joystick/03_named_controls_usb.py)

```bash
python examples/documentation/joystick/03_named_controls_usb.py
```

```python
from asmagic import JoystickDataSubscriber

IPHONE_IP = "usb"  # Use usb:DEVICE_UDID to select a specific iPhone.


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

## All named controller data (Network)

Source: [joystick/02_full_controller.py](../../examples/documentation/joystick/02_full_controller.py)

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

## All named controller data (USB)

Source: [joystick/02_full_controller_usb.py](../../examples/documentation/joystick/02_full_controller_usb.py)

```bash
python examples/documentation/joystick/02_full_controller_usb.py
```

```python
from asmagic import JoystickDataSubscriber

IPHONE_IP = "usb"  # Use usb:DEVICE_UDID to select a specific iPhone.


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

## Old API: sticks and numbered buttons (Network)

Source: [joystick/01_sticks_and_buttons.py](../../examples/documentation/joystick/01_sticks_and_buttons.py)

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

## Old API: sticks and numbered buttons (USB)

Source: [joystick/01_sticks_and_buttons_usb.py](../../examples/documentation/joystick/01_sticks_and_buttons_usb.py)

```bash
python examples/documentation/joystick/01_sticks_and_buttons_usb.py
```

```python
from asmagic import JoystickDataSubscriber

IPHONE_IP = "usb"  # Use usb:DEVICE_UDID to select a specific iPhone.


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
