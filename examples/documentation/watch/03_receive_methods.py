from asmagic import WatchIMUReceiver



def main():
    sub = WatchIMUReceiver(host="0.0.0.0")
    try:
        while True:
            frame = sub.receive()
            for sample in frame.frames:
                print("Time:", sample.timestamp)
                print("Attitude:", sample.attitude)
                print("Rotation rate (rad/s):", sample.rotation_rate)
                print("Gravity (G):", sample.gravity)
                print("Acceleration (G):", sample.acceleration)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
