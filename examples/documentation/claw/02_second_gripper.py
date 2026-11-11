from asmagic import ClawDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def main():
    sub = ClawDataSubscriber(IPHONE_IP, port=5401)
    try:
        while True:
            frame = sub.receive()
            print("Time:", frame.timestamp)
            print("Gripper command (%):", frame.angle)
            print("Motor:", frame.motor)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
