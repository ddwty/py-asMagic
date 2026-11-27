import cv2
from asmagic import ARDataSubscriber

IPHONE_IP = "usb"  # Use usb:DEVICE_UDID to select a specific iPhone.


def main(ip=IPHONE_IP):
    sub = ARDataSubscriber(ip)
    try:
        while True:
            frame = sub.receive()
            frame.show_images()
            if cv2.waitKey(1) & 255 == 27:
                break
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
