from asmagic import HandPoseDataSubscriber, HandTrackingWindow

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.
SHOW_SKELETON = True


def main():
    sub = HandPoseDataSubscriber(IPHONE_IP)
    viewer = None
    try:
        viewer = HandTrackingWindow(labels=True, min_confidence=0.5) if SHOW_SKELETON else None
        while True:
            frame = sub.receive(timeout=50)
            if viewer is not None:
                if not viewer.is_open:
                    break
                viewer.update(frame)
            if frame is None:
                continue
            print("Time:", frame.timestamp)
            print("Left hand detected:", frame.left is not None)
            print("Right hand detected:", frame.right is not None)
    except (KeyboardInterrupt, StopIteration):
        pass
    finally:
        if viewer is not None:
            viewer.close()
        sub.close()


if __name__ == "__main__":
    main()
