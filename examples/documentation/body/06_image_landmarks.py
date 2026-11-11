import numpy as np
from asmagic import BodyTrackingDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.
MODEL = "mediapipe"  # Image landmarks are available with MediaPipe.


def main():
    sub = BodyTrackingDataSubscriber(IPHONE_IP, model=MODEL)
    try:
        while True:
            frame = sub.receive()
            width, height = frame.image_width, frame.image_height
            print("\nImage size (width, height):", (width, height))
            if not frame.people:
                print("No person detected in this frame")
                continue
            for person in frame.people:
                image = person.skeleton(space="image")
                print(f"\nPerson {person.label} (ID: {person.id})")
                print("All 33 landmark names:", image.names)
                print("Normalized image positions [x, y]:\n", image.positions)
                print("Position available:", image.valid)
                if width is not None and height is not None and width > 0 and height > 0:
                    pixels = image.positions * np.array([width, height])
                    print("Pixel positions for available landmarks:\n", pixels[image.valid])
                else:
                    print("Image size unavailable; skip pixel conversion")
                print("Visibility:", image.visibility)
                print("Presence:", image.presence)
    except (KeyboardInterrupt, StopIteration):
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
