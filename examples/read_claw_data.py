"""Run: python examples/read_claw_data.py IPHONE_IP"""
from asmagic import ClawDataSubscriber
from _common import run


def describe(frame):
    print("Time:", frame.timestamp)
    print("Gripper command (%):", frame.angle)
    print("Motor:", frame.motor)


if __name__ == "__main__":
    run(ClawDataSubscriber, describe, "Receive ClawData data")
