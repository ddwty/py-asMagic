"""Shared command-line receive loop used by runnable examples."""
import argparse


def run(subscriber_type, describe, description, plotting=False):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("ip", help="Sender IP address or hostname")
    parser.add_argument("--port", type=int, help="Override the stream's default port")
    parser.add_argument("--count", type=int, default=0, help="Stop after this many frames; 0 runs until Ctrl-C")
    if plotting:
        parser.add_argument("--plot", action="store_true", help="Show tracking plot; off by default")
        parser.add_argument("--space", choices=("body", "world"), default="body", help="3D body coordinate space")
    args = parser.parse_args()
    options = {"port": args.port} if args.port is not None else {}
    sub = subscriber_type(args.ip, **options)
    viewer = None
    count = 0
    try:
        if plotting and args.plot:
            from asmagic import TrackingPlotter
            viewer = TrackingPlotter(space=args.space)
        while viewer is None or viewer.is_open:
            frame = sub.receive(timeout=50) if viewer is not None else sub.receive()
            if frame is None:
                if viewer is not None:
                    viewer.idle()
                continue
            if viewer is not None:
                if not viewer.is_open:
                    break
                viewer.update(frame)
            describe(frame)
            count += 1
            if args.count > 0 and count >= args.count:
                break
    except (KeyboardInterrupt, StopIteration):
        pass
    finally:
        if viewer is not None:
            viewer.close()
        sub.close()
