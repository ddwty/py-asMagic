"""Run with --channel face or --channel hand; use separate terminals for both."""
import argparse
from asmagic import FaceDataSubscriber, HandPoseDataSubscriber


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ip", help="iPhone IP address")
    parser.add_argument("--channel", choices=("face", "hand"), default="face")
    args = parser.parse_args()
    subscriber_type = FaceDataSubscriber if args.channel == "face" else HandPoseDataSubscriber
    sub = subscriber_type(args.ip)
    try:
        while True:
            frame = sub.receive()
            print("Time:", frame.timestamp)
            if args.channel == "face":
                print("Face detected:", frame.has_face)
                print("Face points:", frame.points)
                print("Expressions:", frame.blendshapes)
            else:
                print("Hand count:", frame.hand_count)
                print("Left hand:", frame.left_hand)
                print("Right hand:", frame.right_hand)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
