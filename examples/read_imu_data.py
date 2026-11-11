"""Run: python examples/read_imu_data.py IPHONE_IP"""
from asmagic import IMUDataSubscriber
from _common import run


def describe(frame):
    print("Time:", frame.timestamp)
    print("Accelerometer (G):", frame.accelerometer)
    print("Gyroscope (rad/s):", frame.gyroscope)
    print("Magnetometer (μT):", frame.magnetometer)
    print("Gravity (G):", frame.gravity)
    print("User acceleration (G):", frame.user_acceleration)
    print("Attitude:", frame.attitude)


if __name__ == "__main__":
    run(IMUDataSubscriber, describe, "Receive IMUData data")
