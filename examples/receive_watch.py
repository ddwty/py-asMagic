"""Listen for Watch HTTP protobuf batches; configure the Watch with this computer's IP."""
import argparse
from asmagic import WatchIMUReceiver


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1", help="Bind interface; use 0.0.0.0 for local-network senders")
    parser.add_argument("--port", type=int, default=8002)
    parser.add_argument("--all-batches", action="store_true", help="Queue up to 32 batches instead of conflating")
    parser.add_argument("--format", choices=["batch", "single", "legacy"], default="batch")
    args = parser.parse_args()
    sub = WatchIMUReceiver(args.host, args.port, conflate=not args.all_batches, payload_format=args.format)
    try:
        print("Listening on", sub.address)
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
