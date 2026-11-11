"""Save the next decoded camera image as a PNG."""
import time

import cv2

from asmagic import CameraDataSubscriber

IPHONE_IP = "192.168.1.100"
OUTPUT_PATH = "camera.png"


def main():
    deadline = time.monotonic() + 5
    with CameraDataSubscriber(IPHONE_IP, conflate=True) as sub:
        while time.monotonic() < deadline:
            data = sub.receive(timeout=100)
            if data is None or not data.has_color_image:
                continue
            rgb = data.color_upright
            if rgb is None:
                continue
            bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
            if not cv2.imwrite(OUTPUT_PATH, bgr):
                raise OSError("Could not save " + OUTPUT_PATH)
            print("Saved", OUTPUT_PATH, rgb.shape)
            return
    raise TimeoutError("No camera image arrived. Enable Camera and Stream Video in the app.")


if __name__ == "__main__":
    main()
