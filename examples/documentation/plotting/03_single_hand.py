from asmagic import TrackingPlotter
from asmagic import HandPoseDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def main():
    sub = HandPoseDataSubscriber(IPHONE_IP)
    viewer = TrackingPlotter()
    try:
        while True:
            frame = sub.receive()
            hand = frame.left_hand
            if hand is not None:
                viewer.update(hand)
                print("Time:", frame.timestamp)
                print("Left hand points:", hand.as_arrays().points)
            else:
                viewer.idle()
            if not viewer.is_open:
                break
    except KeyboardInterrupt:
        pass
    finally:
        viewer.close()
        sub.close()


if __name__ == "__main__":
    main()
