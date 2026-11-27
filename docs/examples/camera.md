# Camera Streaming

Code copied verbatim from [the GitBook chapter](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/camera-data-receiving-examples). See that chapter for setup, data formats and limitations.

## Read camera image data (Network)

Source: [camera/00_receive_image_data.py](../../examples/documentation/camera/00_receive_image_data.py)

```bash
python examples/documentation/camera/00_receive_image_data.py
```

```python
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
```

## Read camera image data (USB)

Source: [camera/00_receive_image_data_usb.py](../../examples/documentation/camera/00_receive_image_data_usb.py)

```bash
python examples/documentation/camera/00_receive_image_data_usb.py
```

```python
"""Read camera metadata and access the encoded RGB image bytes."""
from asmagic import CameraDataSubscriber

IPHONE_IP = "usb"


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
```

## Live video preview (Network)

Source: [camera/01_preview.py](../../examples/documentation/camera/01_preview.py)

```bash
python examples/documentation/camera/01_preview.py
```

```python
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
```

## Live video preview (USB)

Source: [camera/01_preview_usb.py](../../examples/documentation/camera/01_preview_usb.py)

```bash
python examples/documentation/camera/01_preview_usb.py
```

```python
"""Display upright video from Stream > Camera > Stream Video."""
import cv2

from asmagic import CameraDataSubscriber

IPHONE_IP = "usb"


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
```

## Receive JPEG images (Network)

Source: [camera/04_jpeg_bytes.py](../../examples/documentation/camera/04_jpeg_bytes.py)

```bash
python examples/documentation/camera/04_jpeg_bytes.py
```

```python
from pathlib import Path
from asmagic import CameraDataSubscriber

with CameraDataSubscriber("192.168.1.100") as camera:
    frame = camera.receive()
    if frame.rgb_codec_name != "jpeg":
        raise ValueError("Select JPEG in Send settings → Encoding.")
    Path("frame.jpg").write_bytes(frame.color_bytes)
```

## Read RGB arrays and timestamps (Network)

Source: [camera/02_rgb_arrays.py](../../examples/documentation/camera/02_rgb_arrays.py)

```bash
python examples/documentation/camera/02_rgb_arrays.py
```

```python
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
```

## Read RGB arrays and timestamps (USB)

Source: [camera/02_rgb_arrays_usb.py](../../examples/documentation/camera/02_rgb_arrays_usb.py)

```bash
python examples/documentation/camera/02_rgb_arrays_usb.py
```

```python
"""Read RGB arrays, image dimensions and capture timestamps."""
from asmagic import CameraDataSubscriber

IPHONE_IP = "usb"


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
```

## Save one image (Network)

Source: [camera/03_save_image.py](../../examples/documentation/camera/03_save_image.py)

```bash
python examples/documentation/camera/03_save_image.py
```

```python
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
```

## Save one image (USB)

Source: [camera/03_save_image_usb.py](../../examples/documentation/camera/03_save_image_usb.py)

```bash
python examples/documentation/camera/03_save_image_usb.py
```

```python
"""Save the next decoded camera image as a PNG."""
import time

import cv2

from asmagic import CameraDataSubscriber

IPHONE_IP = "usb"
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
```
