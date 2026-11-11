from asmagic import MagiClawDataSubscriber

IPHONE_IP = "192.168.1.100"


def main():
    sub = None
    try:
        port = int(input("Enter your legacy MagiClaw publisher's TCP port: "))
        sub = MagiClawDataSubscriber(IPHONE_IP, port=port)
        while True:
            message = sub.receive()
            print('Timestamp:', message.timestamp)
            for name in ('claw', 'finger_0', 'finger_1', 'phone'):
                if message.HasField(name):
                    print(name, getattr(message, name))
    except KeyboardInterrupt:
        pass
    finally:
        if sub is not None:
            sub.close()


if __name__ == "__main__":
    main()
