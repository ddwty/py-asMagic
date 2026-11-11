# AR Data Receiving Examples

Camera images, depth, pose and velocity.

[All examples](index.md) · [Data format and API](api-reference.md)

Replace `IPHONE_IP` with your iPhone's IP and start the matching App output. For Watch, enter your computer's IP on Watch. Ctrl-C stops receiving.

## Example 1: Continuous AR data reading

Print RGB, depth, confidence, poses, intrinsics and frame information. frame.depth keeps the original uint16 values. Missing image arrays are None.

Source: [ar/01_continuous.py](../../examples/documentation/ar/01_continuous.py)

Run from the SDK project directory:

```bash
python examples/documentation/ar/01_continuous.py
```

```python
from asmagic import ARDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def main():
    sub = ARDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive()
            print("Time:", frame.timestamp)
            print("Frame ID:", frame.frame_id)
            print("Capture time:", frame.source_timestamp)

            print("RGB:", frame.color_array)
            print("RGB size:", frame.rgb_width, frame.rgb_height)
            print("Depth (raw):", frame.depth)
            print("Depth size:", frame.depth_width, frame.depth_height)
            print("Depth confidence:", frame.depth_confidence_array)
            print("Depth scale (m/unit):", frame.depth_meters_per_unit)

            print("Velocity (m/s):", frame.velocity)
            print("Local pose:", frame.local_pose)
            print("Global pose:", frame.global_pose)
            print("Local transform:", frame.local_pose_matrix)
            print("Global transform:", frame.global_pose_matrix)
            print("Intrinsics:", frame.camera_intrinsics)
            print("Intrinsics matrix:", frame.camera_intrinsics_matrix)

            print("Session:", frame.session_identifier)
            print("Shared world:", frame.shared_world_identifier)
            print("Global pose is shared:", frame.global_pose_is_shared)
            print("Has RGB / depth / pose:", frame.has_color_image, frame.has_depth_image, frame.has_pose)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## Example 2: Optionally display color and depth

Choose color and depth with show_images(). ESC closes the windows.

Source: [ar/03_display_images.py](../../examples/documentation/ar/03_display_images.py)

Run from the SDK project directory:

```bash
python examples/documentation/ar/03_display_images.py
```

```python
import cv2
from asmagic import ARDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


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
```

## Example 3: Process RGB, depth and confidence arrays

Arrays retain raw orientation. frame.depth keeps the original uint16 values; missing images are None.

Source: [ar/04_image_arrays.py](../../examples/documentation/ar/04_image_arrays.py)

Run from the SDK project directory:

```bash
python examples/documentation/ar/04_image_arrays.py
```

```python
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
```

## Example 4: Positions, quaternions and matrices

Pose translation is in meters; rotation is [qx, qy, qz, qw].

Source: [ar/05_pose_matrices.py](../../examples/documentation/ar/05_pose_matrices.py)

Run from the SDK project directory:

```bash
python examples/documentation/ar/05_pose_matrices.py
```

```python
from asmagic import ARDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def main():
    sub = ARDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive()
            if frame.local_pose.size == 7:
                print('Position (m):', frame.local_pose[:3])
                print('Quaternion (x/y/z/w):', frame.local_pose[3:])
            print('Local transform:', frame.local_pose_matrix)
            print('Global transform:', frame.global_pose_matrix)
            print('Camera K:', frame.camera_intrinsics_matrix)
            print('Velocity (m/s):', frame.velocity)
            print('Shared world:', frame.global_pose_is_shared, frame.shared_world_identifier)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## Example 5: Frame and session information

Print capture, session and image metadata.

Source: [ar/07_metadata.py](../../examples/documentation/ar/07_metadata.py)

Run from the SDK project directory:

```bash
python examples/documentation/ar/07_metadata.py
```

```python
from asmagic import ARDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def main():
    sub = ARDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive()
            print('Frame ID:', frame.frame_id)
            print('Timestamps:', frame.timestamp, frame.source_timestamp)
            print('RGB dimensions:', frame.rgb_width, frame.rgb_height)
            print('Depth dimensions:', frame.depth_width, frame.depth_height)
            print('Depth scale (m/unit):', frame.depth_meters_per_unit)
            print('Session:', frame.session_identifier)
            print('Shared world:', frame.shared_world_identifier, frame.global_pose_is_shared)
            print('Has RGB / depth / pose:', frame.has_color_image, frame.has_depth_image, frame.has_pose)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## Example 6: Read image and pose fields

Read all values from one received frame.

Source: [ar/08_frame_fields.py](../../examples/documentation/ar/08_frame_fields.py)

Run from the SDK project directory:

```bash
python examples/documentation/ar/08_frame_fields.py
```

```python
from asmagic import ARDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def main():
    sub = ARDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive()
            print("Time:", frame.timestamp)
            print("RGB:", frame.color_array)
            print("Depth:", frame.depth)
            print("Depth size:", frame.depth_width, frame.depth_height)
            print("Local pose:", frame.local_pose)
            print("Global pose:", frame.global_pose)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## Example 7: Scale intrinsics using verified reference dimensions

Set REFERENCE_SIZE to the image size used for the intrinsics.

Source: [ar/09_intrinsics.py](../../examples/documentation/ar/09_intrinsics.py)

Run from the SDK project directory:

```bash
python examples/documentation/ar/09_intrinsics.py
```

```python
from asmagic import ARDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def main():
    sub = ARDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive()
            print("Time:", frame.timestamp)
            print("Velocity:", frame.velocity)
            print("Local pose:", frame.local_pose)
            print("Global pose:", frame.global_pose)
            print("Intrinsics:", frame.camera_intrinsics)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## Example 8: Original camera intrinsics scaling example

Scale fx, fy, cx and cy from 1920 x 1440 to 640 x 480.

Source: [ar/10_selected_fields.py](../../examples/documentation/ar/10_selected_fields.py)

Run from the SDK project directory:

```bash
python examples/documentation/ar/10_selected_fields.py
```

```python
from asmagic import ARDataSubscriber
import numpy as np

sub = ARDataSubscriber("192.168.1.100")

for data in sub:
    K = np.array(data.camera_intrinsics).reshape(3, 3, order='F')
    scale_x = 640 / 1920  # = 1/3
    scale_y = 480 / 1440  # = 1/3

    K[0, 0] *= scale_x  # fx
    K[1, 1] *= scale_y  # fy
    K[0, 2] *= scale_x  # cx
    K[1, 2] *= scale_y  # cy

    print(f"Scaled intrinsics:\n{K}")
```

## Example 9: Quick Start AR receiving example

AR quick start using direct frame fields.

Source: [ar/11_quick_start.py](../../examples/documentation/ar/11_quick_start.py)

Run from the SDK project directory:

```bash
python examples/documentation/ar/11_quick_start.py
```

```python
from asmagic import ARDataSubscriber

# Create subscriber with your iPhone's IP address
sub = ARDataSubscriber("192.168.1.100")

try:
    # Continuous data streaming
    for data in sub:
        # All sensor data in one frame
        print(f"Timestamp: {data.timestamp}")
        print(f"Velocity: {data.velocity}")
        print(f"Local Pose: {data.local_pose}")
        print(f"Global Pose: {data.global_pose}")
        print(f"Camera Intrinsics: {data.camera_intrinsics}")

        # Access image data
        if data.has_color_image:
            # Color: bytes(jpeg format) or array
            color_bytes = data.color_bytes
            color_array = data.color_array  # or shortcut: data.color
            print(f"Color: {len(color_bytes)} bytes, array shape: {color_array.shape}")

        if data.has_depth_image:
            # Depth: Numpy array
            depth = data.depth_array  # or shortcut: data.depth
            print(f"Depth: {depth.shape}")

except KeyboardInterrupt:
    print("\nStopped by user")
finally:
    sub.close()
```

## Example 10: Authored AR continuous receiving example

The AR guide retains this original top-level receiving loop; edit its IP before running.

Source: [ar/12_authored_continuous.py](../../examples/documentation/ar/12_authored_continuous.py)

Run from the SDK project directory:

```bash
python examples/documentation/ar/12_authored_continuous.py
```

```python
from asmagic import ARDataSubscriber

# Create subscriber with your iPhone's IP address
sub = ARDataSubscriber("192.168.1.100")

try:
    # Continuous data streaming
    while True:
        data = sub.receive()
        # All sensor data in one frame
        print(f"Timestamp: {data.timestamp}")
        print(f"Velocity: {data.velocity}")
        print(f"Local Pose: {data.local_pose}")
        print(f"Global Pose: {data.global_pose}")
        print(f"Camera Intrinsics: {data.camera_intrinsics}")

        # Access image data
        if data.has_color_image:
            # Color: bytes(jpeg format) or array
            color_bytes = data.color_bytes
            color_array = data.color_array  # or shortcut: data.color
            print(f"Color: {len(color_bytes)} bytes, array shape: {color_array.shape}")

        if data.has_depth_image:
            # Depth: Numpy array
            depth = data.depth
            print(f"Depth: {depth.shape}")

        # Additional fields; all original properties above remain unchanged.
        print(f"Frame ID: {data.frame_id}")
        print(f"Capture Timestamp: {data.source_timestamp}")
        print(f"RGB Size: {data.rgb_width}, {data.rgb_height}")
        print(f"RGB Codec: {data.rgb_codec_name}")
        print(f"Depth Size: {data.depth_width}, {data.depth_height}")
        print(f"Depth Confidence: {data.depth_confidence_array}")
        print(f"Depth Scale (m/unit): {data.depth_meters_per_unit}")

        # Display rotation only. Upright depth still uses raw uint16 units.
        print(f"Upright RGB: {data.color_upright}")
        print(f"Upright depth: {data.depth_upright}")
        print(f"Image Rotation (clockwise quarter turns): {data.image_rotation_quarter_turns_clockwise}")

        # Added matrix properties; the original pose/intrinsics arrays stay unchanged.
        print(f"Local Pose Matrix: {data.local_pose_matrix}")
        print(f"Global Pose Matrix: {data.global_pose_matrix}")
        print(f"Camera Intrinsics Matrix: {data.camera_intrinsics_matrix}")
        print(f"Session: {data.session_identifier}")
        print(f"Shared World: {data.shared_world_identifier}")
        print(f"Global Pose Is Shared: {data.global_pose_is_shared}")

except KeyboardInterrupt:
    print("\nStopped by user")
finally:
    sub.close()
```
