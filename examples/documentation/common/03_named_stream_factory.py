from asmagic import STREAMS, subscribe

IPHONE_IP = "192.168.1.100"
STREAM_NAME = "hand"


def main():
    for name, info in STREAMS.items():
        print(name, info.subscriber.__name__, info.port, info.message, info.feature)
    sub = subscribe(STREAM_NAME, IPHONE_IP, verbose=True)
    try:
        while True:
            frame = sub.receive()
            print(type(frame).__name__, frame.timestamp)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
