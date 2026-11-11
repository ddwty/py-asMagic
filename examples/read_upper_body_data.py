"""Run: python examples/read_upper_body_data.py IPHONE_IP"""
from asmagic import BodyPoseDataSubscriber
from _common import run


def describe(frame):
    print("Time:", frame.timestamp)
    print("Upper body:", frame.upper_body)
    print("Detection FPS:", frame.detection_fps)


if __name__ == "__main__":
    run(BodyPoseDataSubscriber, describe, "Receive BodyPoseData data", plotting=True)
