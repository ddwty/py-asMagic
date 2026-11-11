"""Run: python examples/read_hand_data.py IPHONE_IP"""
from asmagic import HandPoseDataSubscriber
from _common import run


def describe(frame):
    print("Time:", frame.timestamp)
    print("Hand count:", frame.hand_count)
    print("Left hand:", frame.left_hand)
    print("Right hand:", frame.right_hand)


if __name__ == "__main__":
    run(HandPoseDataSubscriber, describe, "Receive HandPoseData data", plotting=True)
