"""Receive any known ZeroMQ stream. Use --help for stream names and options."""
import argparse
from asmagic import STREAMS, subscribe


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stream", choices=sorted(STREAMS))
    parser.add_argument("ip", help="Sender IP address")
    parser.add_argument("--port", type=int)
    parser.add_argument("--count", type=int, default=0)
    args = parser.parse_args()
    options = {"port": args.port} if args.port is not None else {}
    sub = subscribe(args.stream, args.ip, **options)
    count = 0
    try:
        while True:
            frame = sub.receive()
            print("Frame:", frame)
            count += 1
            if args.count > 0 and count >= args.count:
                break
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
