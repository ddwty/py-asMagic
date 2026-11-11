from asmagic import JoystickDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def main():
    sub = JoystickDataSubscriber(IPHONE_IP)
    try:
        while True:
            data = sub.receive()
            print("Time:", data.timestamp)
            print("Left joystick:", data.left_x, data.left_y)
            print("Right joystick:", data.right_x, data.right_y)
            if data.button.square:
                print("Square held")
            print("L1/R1:", data.button.l1, data.button.r1)
            print("L2/R2:", data.button.l2, data.button.r2)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
