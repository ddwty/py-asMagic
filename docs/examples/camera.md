# Camera Streaming Examples

Receive RGB video from the camera lens selected on your iPhone. Install `asmagic` 1.0.2 or newer.

## Set up the iPhone

- Connect your iPhone and computer to the same network.
- Open **Stream**. It starts in **Camera + AR**, so select **Camera** for this receiver.
- Choose a lens. **0.5×** selects the ultra-wide camera on supported iPhones. Use the camera-switch button for the front camera.
- Open **Send settings**, choose a **Resolution**, then enable **Stream Video**.
- Copy the displayed **IP address** into `IPHONE_IP` in the example.

The flashlight button controls the current rear camera when supported.

## Resolution and orientation

The resolution list shows the pixel dimensions sent to Python. Available choices follow the selected lens and device orientation. A 1920 × 1080 camera frame offers 320 × 180, 640 × 360, 960 × 540, 1280 × 720 and 1920 × 1080 px. Portrait output swaps width and height. Check `data.rgb_width`, `data.rgb_height` or `data.color_upright.shape` after changing lenses or resolution.

The sender rotates images and mirrors the front camera to match its preview. Frames use JPEG or HEVC, and `color_bytes` returns the compressed payload. The SDK decodes either format into RGB pixels in `data.color_array`. Use `data.color_upright` to apply rotation metadata or `data.show_image()` to display an upright image.

`CameraDataSubscriber.receive()` returns one `CameraFrame`. Its `has_color_image`, `color_bytes`, `color_array` and `color_upright` fields match the `ARFrame` image API. Camera uses port 8105; AR uses port 8000. Camera frames have no pose, intrinsics or depth.

## Frame data

| Field | Value |
|---|---|
| `color_array`, `color_upright` | RGB `uint8` NumPy array shaped `(height, width, 3)`, or `None` while waiting for a decodable image; same access as AR frames |
| `image`, `image_upright` | Backward-compatible aliases for `color_array` and `color_upright` |
| `rgb_width`, `rgb_height` | Encoded width and height in pixels; `width` and `height` are aliases |
| `timestamp` | iPhone wall-clock time in seconds |
| `source_timestamp` | Monotonic camera capture time in seconds |
| `frame_id` | Frame sequence number, which restarts when the sender changes lens, resolution or session |
| `color_bytes` | Encoded JPEG or HEVC bytes; `image_bytes` is an alias |
| `has_color_image` | Whether the frame contains encoded color image bytes |
| `protobuf` | Original message for advanced inspection |

`CameraDataSubscriber(ip, port=8105, hwm=32, conflate=False, verbose=False)` supports context management, `receive()`, `receive(timeout=...)`, iteration and `close()`. A timeout is in milliseconds and returns `None`. `subscribe("camera", ip)` selects the same receiver.

The receiver decodes HEVC packets in order. `conflate=True` keeps the latest decoded frame for a responsive preview. Continue receiving after a lens or resolution change while the next keyframe arrives. The examples below keep the video window responsive during a pause and release their receiver when stopped.

```bash
python -m pip install --upgrade "asmagic>=1.0.2"
```


[All examples](index.md) · [Data format and API](api-reference.md)

## Read camera image data

Read frame metadata and access the encoded image bytes.

Source: [camera/00_receive_image_data.py](../../examples/documentation/camera/00_receive_image_data.py)

Run from the SDK project directory:

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

## Live video preview

Press Q or Escape in the video window to close it. Ctrl-C stops the receiver from the terminal.

Source: [camera/01_preview.py](../../examples/documentation/camera/01_preview.py)

Run from the SDK project directory:

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

## Read RGB arrays and timestamps

Read the RGB image in received orientation using the same `color_array` property as AR frames. Ctrl-C stops receiving.

Source: [camera/02_rgb_arrays.py](../../examples/documentation/camera/02_rgb_arrays.py)

Run from the SDK project directory:

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

## Save one image

Save camera.png in the current directory. The script waits up to five seconds for a decoded frame.

Source: [camera/03_save_image.py](../../examples/documentation/camera/03_save_image.py)

Run from the SDK project directory:

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
