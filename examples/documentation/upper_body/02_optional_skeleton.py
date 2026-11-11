from asmagic import TrackingPlotter
from asmagic import BodyPoseDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.
SHOW_SKELETON = True


def main():
    sub = BodyPoseDataSubscriber(IPHONE_IP)
    viewer = TrackingPlotter() if SHOW_SKELETON else None
    try:
        while True:
            frame = sub.receive()
            if viewer is not None:
                if not viewer.is_open:
                    break
                viewer.update(frame)
            print("Time:", frame.timestamp)
            print("Upper body:", frame.upper_body)
    except KeyboardInterrupt:
        pass
    finally:
        if viewer is not None:
            viewer.close()
        sub.close()


if __name__ == "__main__":
    main()
