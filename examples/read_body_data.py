"""Run: python examples/read_body_data.py IPHONE_IP --model mediapipe [--plot]"""
import argparse
from asmagic import BodyTrackingDataSubscriber, TrackingPlotter


def describe(frame):
    print("Time:", frame.timestamp)
    print("Tracking:", frame.tracking_state)
    print("People:", frame.person_count)
    for person in frame.people:
        body = person.skeleton()
        print("Person:", person.id)
        print("Joint names:", body.names)
        print("Positions (m):", body.positions)
        print("Valid positions:", body.valid)
        print("Rotations:", body.rotations)
        print("Valid rotations:", body.rotation_valid)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ip", help="iPhone hostname or IP")
    parser.add_argument("--model", choices=("arkit", "mediapipe"), default="mediapipe",
                        help="Match the recognition model selected in the App")
    parser.add_argument("--plot", action="store_true")
    parser.add_argument("--space", choices=("body", "world"), default="body")
    args = parser.parse_args()
    sub = BodyTrackingDataSubscriber(args.ip, model=args.model)
    viewer = TrackingPlotter(space=args.space) if args.plot else None
    try:
        while viewer is None or viewer.is_open:
            frame = sub.receive(timeout=50 if viewer is not None else 1000)
            if frame is None:
                if viewer is not None:
                    viewer.idle()
                continue
            describe(frame)
            if viewer is not None:
                viewer.update(frame)
    except (KeyboardInterrupt, StopIteration):
        pass
    finally:
        sub.close()
        if viewer is not None:
            viewer.close()


if __name__ == "__main__":
    main()
