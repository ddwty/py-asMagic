from asmagic import JoystickDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def main():
    sub = JoystickDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive()
            print("Time:", frame.timestamp)
            print("Left joystick:", frame.left_x, frame.left_y)
            print("Right joystick:", frame.right_x, frame.right_y)
            print("Triangle:", frame.button1)
            print("Square:", frame.button2)
            print("Cross:", frame.button3)
            print("Circle:", frame.button4)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
