from asmagic import BodyPoseDataSubscriber

IPHONE_IP = "usb"  # Use usb:DEVICE_UDID to select a specific iPhone.


def main():
    sub = BodyPoseDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive()
            print("Time:", frame.timestamp)
            print("Upper body:", frame.upper_body)
            print("Detection FPS:", frame.detection_fps)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
