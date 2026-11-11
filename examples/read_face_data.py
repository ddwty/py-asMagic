"""Run: python examples/read_face_data.py IPHONE_IP"""
from asmagic import FaceDataSubscriber
from _common import run


def describe(frame):
    print("Time:", frame.timestamp)
    print("Face detected:", frame.has_face)
    print("Face points:", frame.points)
    print("Expressions:", frame.blendshapes)
    print("Position (m):", frame.camera_position_meters)
    print("Orientation:", frame.camera_orientation)


if __name__ == "__main__":
    run(FaceDataSubscriber, describe, "Receive FaceData data", plotting=True)
