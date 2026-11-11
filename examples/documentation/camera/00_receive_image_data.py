"""Read camera metadata and access the encoded RGB image bytes."""
from asmagic import CameraDataSubscriber

IPHONE_IP = "192.168.1.100"


def main():
    sub = CameraDataSubscriber(IPHONE_IP)
    try:
        while True:
            data = sub.receive()
            print(f"Timestamp: {data.timestamp}")
            print(f"Frame ID: {data.frame_id}")
            print(f"Image size: {data.rgb_width} x {data.rgb_height}")

            if data.has_color_image:
                color_bytes = data.color_bytes
                print(f"Color image: {len(color_bytes)} encoded bytes")
    except (KeyboardInterrupt, StopIteration):
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
