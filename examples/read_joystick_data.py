"""Run: python examples/read_joystick_data.py IPHONE_IP"""
from asmagic import JoystickDataSubscriber
from _common import run


def describe(data):
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


if __name__ == "__main__":
    run(JoystickDataSubscriber, describe, "Receive joystick input")
