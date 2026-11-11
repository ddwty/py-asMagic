"""Run: python examples/read_airpods_data.py IPHONE_IP"""
from asmagic import AirPodsDataSubscriber
from _common import run


def describe(frame):
    print("Time:", frame.timestamp)
    print("Rotation:", frame.rotation)


if __name__ == "__main__":
    run(AirPodsDataSubscriber, describe, "Receive AirPodsData data")
