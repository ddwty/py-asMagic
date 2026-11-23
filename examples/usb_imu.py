"""Receive USB IMU data: python examples/usb_imu.py. Start IMU in the app."""
import asmagic


def main():
    with asmagic.IMUDataSubscriber("usb") as sub:
        while True:
            frame = sub.receive(timeout=1000)
            if frame is None:
                print(sub.last_error or "Waiting for iPhone IMU; open asMagic and start IMU streaming.")
            else:
                print(frame.timestamp, frame.accelerometer, frame.gyroscope)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
