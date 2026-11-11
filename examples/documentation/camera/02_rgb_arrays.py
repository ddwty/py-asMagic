"""Read RGB arrays, image dimensions and capture timestamps."""
from asmagic import CameraDataSubscriber

IPHONE_IP = "192.168.1.100"


def main():
    try:
        with CameraDataSubscriber(IPHONE_IP, conflate=True) as sub:
            while True:
                data = sub.receive(timeout=1000)
                if data is None or not data.has_color_image:
                    continue
                rgb = data.color_array
                if rgb is None:
                    continue
                height, width, channels = rgb.shape
                print("RGB", width, height, channels, rgb.dtype)
                print("frame_id", data.frame_id)
                print("timestamp", data.timestamp)
                print("source_timestamp", data.source_timestamp)
                print("first_pixel_rgb", rgb[0, 0].tolist())
    except (KeyboardInterrupt, StopIteration):
        pass


if __name__ == "__main__":
    main()
