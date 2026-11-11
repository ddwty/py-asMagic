from asmagic import IMUDataSubscriber

IPHONE_IP = "192.168.1.100"


def on_frame(frame):
    print(frame.timestamp, frame.gyroscope)


def main():
    sub = IMUDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive()
            on_frame(frame)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
