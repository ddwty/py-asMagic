from asmagic import WatchIMUReceiver

PAYLOAD_FORMAT = "batch"  # "batch", "single" or "legacy".


def main():
    sub = WatchIMUReceiver(host="0.0.0.0", payload_format=PAYLOAD_FORMAT)
    try:
        while True:
            frame = sub.receive()
            message = frame.protobuf
            decoded = sub.decode(message.SerializeToString())
            print("Batch time:", decoded.timestamp)
            print("Samples:", decoded.frames)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
