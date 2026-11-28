# AR Data

Code copied verbatim from [the GitBook chapter](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/ar-data-receiving-examples). See that chapter for setup, data formats and limitations.

## Read all AR fields (Network)

Source: [ar/01_continuous.py](../../examples/documentation/ar/01_continuous.py)

```bash
python examples/documentation/ar/01_continuous.py
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
            # Encoded payload and optional decoded RGB image
            color_bytes = data.color_bytes
            color_array = data.color_array  # or shortcut: data.color
            shape = color_array.shape if color_array is not None else None
            print(f"Color: {len(color_bytes)} bytes, array shape: {shape}")

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

## Read all AR fields (USB)

Source: [ar/01_continuous_usb.py](../../examples/documentation/ar/01_continuous_usb.py)

```bash
python examples/documentation/ar/01_continuous_usb.py
```

```python
from asmagic import ARDataSubscriber

# Receive from the USB-connected iPhone
sub = ARDataSubscriber("usb")

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
            # Encoded payload and optional decoded RGB image
            color_bytes = data.color_bytes
            color_array = data.color_array  # or shortcut: data.color
            shape = color_array.shape if color_array is not None else None
            print(f"Color: {len(color_bytes)} bytes, array shape: {shape}")

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

## Optionally display color and depth (Network)

Source: [ar/03_display_images.py](../../examples/documentation/ar/03_display_images.py)

```bash
python examples/documentation/ar/03_display_images.py
```

```python
import cv2
from asmagic import ARDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def main(ip=IPHONE_IP):
    sub = ARDataSubscriber(ip, conflate=True)
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

## Optionally display color and depth (USB)

Source: [ar/03_display_images_usb.py](../../examples/documentation/ar/03_display_images_usb.py)

```bash
python examples/documentation/ar/03_display_images_usb.py
```

```python
import cv2
from asmagic import ARDataSubscriber

IPHONE_IP = "usb"  # Use usb:DEVICE_UDID to select a specific iPhone.


def main(ip=IPHONE_IP):
    sub = ARDataSubscriber(ip, conflate=True)
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

## Process RGB, depth and confidence arrays (Network)

Source: [ar/04_image_arrays.py](../../examples/documentation/ar/04_image_arrays.py)

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

## Process RGB, depth and confidence arrays (USB)

Source: [ar/04_image_arrays_usb.py](../../examples/documentation/ar/04_image_arrays_usb.py)

```bash
python examples/documentation/ar/04_image_arrays_usb.py
```

```python
from asmagic import ARDataSubscriber

IPHONE_IP = "usb"  # Use usb:DEVICE_UDID to select a specific iPhone.


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

## Positions, quaternions and matrices (Network)

Source: [ar/05_pose_matrices.py](../../examples/documentation/ar/05_pose_matrices.py)

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

## Positions, quaternions and matrices (USB)

Source: [ar/05_pose_matrices_usb.py](../../examples/documentation/ar/05_pose_matrices_usb.py)

```bash
python examples/documentation/ar/05_pose_matrices_usb.py
```

```python
from asmagic import ARDataSubscriber

IPHONE_IP = "usb"  # Use usb:DEVICE_UDID to select a specific iPhone.


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

## Read selected AR fields (Network)

Source: [ar/10_selected_fields.py](../../examples/documentation/ar/10_selected_fields.py)

```bash
python examples/documentation/ar/10_selected_fields.py
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

## Read selected AR fields (USB)

Source: [ar/10_selected_fields_usb.py](../../examples/documentation/ar/10_selected_fields_usb.py)

```bash
python examples/documentation/ar/10_selected_fields_usb.py
```

```python
from asmagic import ARDataSubscriber

IPHONE_IP = "usb"  # Use usb:DEVICE_UDID to select a specific iPhone.


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

## Intrinsics and image size (Network)

Source: [ar/09_intrinsics.py](../../examples/documentation/ar/09_intrinsics.py)

```bash
python examples/documentation/ar/09_intrinsics.py
```

```python
from asmagic import ARDataSubscriber

with ARDataSubscriber("192.168.1.100") as sub:
    for data in sub:
        K_rgb = data.camera_intrinsics_matrix
        if K_rgb is None or data.rgb_width <= 0 or data.rgb_height <= 0:
            continue
        print("RGB intrinsics:", K_rgb)
        if data.has_depth_image:
            K_depth = K_rgb.copy()
            K_depth[0, :] *= data.depth_width / data.rgb_width
            K_depth[1, :] *= data.depth_height / data.rgb_height
            print("Registered depth intrinsics:", K_depth)
```

## Intrinsics and image size (USB)

Source: [ar/09_intrinsics_usb.py](../../examples/documentation/ar/09_intrinsics_usb.py)

```bash
python examples/documentation/ar/09_intrinsics_usb.py
```

```python
from asmagic import ARDataSubscriber

with ARDataSubscriber("usb") as sub:
    for data in sub:
        K_rgb = data.camera_intrinsics_matrix
        if K_rgb is None or data.rgb_width <= 0 or data.rgb_height <= 0:
            continue
        print("RGB intrinsics:", K_rgb)
        if data.has_depth_image:
            K_depth = K_rgb.copy()
            K_depth[0, :] *= data.depth_width / data.rgb_width
            K_depth[1, :] *= data.depth_height / data.rgb_height
            print("Registered depth intrinsics:", K_depth)
```
