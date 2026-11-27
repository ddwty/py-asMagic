from asmagic import FaceDataSubscriber

IPHONE_IP = "usb"  # Use usb:DEVICE_UDID to select a specific iPhone.


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
