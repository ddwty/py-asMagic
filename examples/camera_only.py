"""Display upright video from Stream > Camera > Stream Video."""
import cv2

from asmagic import CameraDataSubscriber

IPHONE_IP = "192.168.1.100"


def main():
    sub = CameraDataSubscriber(IPHONE_IP, conflate=True)
    try:
        while True:
            data = sub.receive(timeout=100)
            if data is not None and data.has_color_image:
                data.show_image("asMagic camera")
            if cv2.waitKey(1) & 0xFF in (27, ord("q")):
                break
    except (KeyboardInterrupt, StopIteration):
        pass
    finally:
        sub.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
