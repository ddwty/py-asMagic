from asmagic import LegacyWatchDataSubscriber

IPHONE_IP = "192.168.1.100"


def main():
    sub = None
    try:
        port = int(input("Enter your legacy Watch publisher's TCP port: "))
        sub = LegacyWatchDataSubscriber(IPHONE_IP, port=port)
        while True:
            frame = sub.receive()
            print(frame.timestamp, frame.attitude, frame.rotation_rate, frame.gravity, frame.acceleration)
            offline = LegacyWatchDataSubscriber.decode(frame.protobuf.SerializeToString())
            print('Offline decoded attitude:', offline.attitude)
    except KeyboardInterrupt:
        pass
    finally:
        if sub is not None:
            sub.close()


if __name__ == "__main__":
    main()
