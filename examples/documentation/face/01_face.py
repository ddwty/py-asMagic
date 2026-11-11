from asmagic import FaceDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def main():
    sub = FaceDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive()
            print("Time:", frame.timestamp)
            print("Face detected:", frame.has_face)
            print("Face points:", frame.points)
            print("Expressions:", frame.blendshapes)
            print("Position (m):", frame.camera_position_meters)
            print("Orientation:", frame.camera_orientation)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
