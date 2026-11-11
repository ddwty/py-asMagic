"""Continuously receive camera pose. Run: python examples/simple_continuous.py SENDER_IP"""
from asmagic import ARDataSubscriber
from _common import run


def describe(frame):
    print("Time:", frame.timestamp)
    print("Local pose:", frame.local_pose)
    print("Velocity:", frame.velocity)


if __name__ == "__main__":
    run(ARDataSubscriber, describe, 'Continuously receive camera pose')
