import numpy as np
from asmagic import FaceDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def main():
    sub = FaceDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive()
            if not frame.has_face:
                print('No face in this frame')
                continue
            # A Vision index is unique within its region, not across the face.
            by_region = {}
            for point in frame.landmarks:
                by_region.setdefault(point.region, []).append(point)
            for region, points in by_region.items():
                print(region, 'point IDs:', [point.index for point in points])
            box = frame.image_location
            if box is not None:
                corners = np.array([
                    [box.center_x - box.width / 2, box.center_y - box.height / 2],
                    [box.center_x + box.width / 2, box.center_y + box.height / 2],
                ], dtype=np.float32)
                print('Raw normalized box [top-left, bottom-right]:', corners)
                if frame.image_width > 0 and frame.image_height > 0:
                    size = np.array([frame.image_width, frame.image_height], dtype=np.float32)
                    print('Raw box pixels:', corners * size)
                    print('Raw point pixels:', frame.points * size)
            # These continuous pixel coordinates have not been rotated or mirrored.
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
