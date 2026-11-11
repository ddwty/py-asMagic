from asmagic import ARDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def main():
    sub = ARDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive()
            print("RGB:", frame.color_array)
            print("Depth:", frame.depth)
            print("Confidence:", frame.depth_confidence_array)
            print("Upright RGB:", frame.color_upright)
            print("Upright depth:", frame.depth_upright)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
