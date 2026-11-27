# Face Tracking

Code copied verbatim from [the GitBook chapter](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/face-and-hand-tracking). See that chapter for setup, data formats and limitations.

## Face observations and frame metadata (Network)

Source: [face/01_face.py](../../examples/documentation/face/01_face.py)

```bash
python examples/documentation/face/01_face.py
```

```python
from asmagic import FaceDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def main():
    sub = FaceDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive()
            print("Time:", frame.timestamp)
            print("Face detected:", frame.has_face)
            print("Face points:", frame.points)
            print("Expressions:", frame.blendshapes)
            print("Position (m):", frame.camera_position_meters)
            print("Orientation:", frame.camera_orientation)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## Face observations and frame metadata (USB)

Source: [face/01_face_usb.py](../../examples/documentation/face/01_face_usb.py)

```bash
python examples/documentation/face/01_face_usb.py
```

```python
from asmagic import FaceDataSubscriber

IPHONE_IP = "usb"  # Use usb:DEVICE_UDID to select a specific iPhone.


def main():
    sub = FaceDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive()
            print("Time:", frame.timestamp)
            print("Face detected:", frame.has_face)
            print("Face points:", frame.points)
            print("Expressions:", frame.blendshapes)
            print("Position (m):", frame.camera_position_meters)
            print("Orientation:", frame.camera_orientation)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## All available facial movement coefficients (Network)

Source: [face/02_blendshapes.py](../../examples/documentation/face/02_blendshapes.py)

```bash
python examples/documentation/face/02_blendshapes.py
```

```python
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
            if frame.tracking_mode != 'true_depth':
                print('Blendshapes unavailable in mode:', frame.tracking_mode)
                continue
            print('Coefficient count:', len(frame.blendshapes))
            for name, value in sorted(frame.blendshape_coefficients.items()):
                print(name, value, type(value).__name__)
            # None means the named channel is absent; 0.0 is a received value.
            print('Jaw open:', frame.blendshapes.get('jawOpen'))
            print('Left / right blink:', frame.blendshapes.get('eyeBlinkLeft'), frame.blendshapes.get('eyeBlinkRight'))
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## All available facial movement coefficients (USB)

Source: [face/02_blendshapes_usb.py](../../examples/documentation/face/02_blendshapes_usb.py)

```bash
python examples/documentation/face/02_blendshapes_usb.py
```

```python
from asmagic import FaceDataSubscriber

IPHONE_IP = "usb"  # Use usb:DEVICE_UDID to select a specific iPhone.


def main():
    sub = FaceDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive()
            if not frame.has_face:
                print('No face in this frame')
                continue
            if frame.tracking_mode != 'true_depth':
                print('Blendshapes unavailable in mode:', frame.tracking_mode)
                continue
            print('Coefficient count:', len(frame.blendshapes))
            for name, value in sorted(frame.blendshape_coefficients.items()):
                print(name, value, type(value).__name__)
            # None means the named channel is absent; 0.0 is a received value.
            print('Jaw open:', frame.blendshapes.get('jawOpen'))
            print('Left / right blink:', frame.blendshapes.get('eyeBlinkLeft'), frame.blendshapes.get('eyeBlinkRight'))
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## Read landmark regions and raw bounding-box pixels (Network)

Source: [face/08_regions_and_box.py](../../examples/documentation/face/08_regions_and_box.py)

```bash
python examples/documentation/face/08_regions_and_box.py
```

```python
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
```

## Read landmark regions and raw bounding-box pixels (USB)

Source: [face/08_regions_and_box_usb.py](../../examples/documentation/face/08_regions_and_box_usb.py)

```bash
python examples/documentation/face/08_regions_and_box_usb.py
```

```python
import numpy as np
from asmagic import FaceDataSubscriber

IPHONE_IP = "usb"  # Use usb:DEVICE_UDID to select a specific iPhone.


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
```

## Metric face vertices and triangle topology (Network)

Source: [face/03_metric_mesh.py](../../examples/documentation/face/03_metric_mesh.py)

```bash
python examples/documentation/face/03_metric_mesh.py
```

```python
from asmagic import FaceDataSubscriber
from asmagic.geometry import pose_matrix
import numpy as np

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def main():
    sub = FaceDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive()
            if not frame.has_face:
                print('No face in this frame')
                continue
            print('Flat triangle IDs:', frame.triangle_indices)
            vertices = frame.face_vertices
            if vertices is None or frame.tracking_mode != 'true_depth':
                print('Metric face mesh unavailable')
                continue
            row_by_id = {point.index: row for row, point in enumerate(frame.landmarks)}
            triangle_rows = np.array([
                [row_by_id[int(vertex)] for vertex in triangle]
                for triangle in frame.triangles
                if all(int(vertex) in row_by_id for vertex in triangle)
            ], dtype=np.int32).reshape(-1, 3)
            print('Vertices (m):', vertices)
            print('Triangle row indices:', triangle_rows)
            print('Triangle vertex coordinates (M x 3 x 3):', vertices[triangle_rows])
            position = frame.camera_position_meters
            orientation = frame.camera_orientation
            if position is not None and orientation is not None:
                # Face-local -> camera coordinates, in meters; no image mirroring.
                camera_from_face = pose_matrix(np.concatenate([position, orientation]))
                camera_vertices = vertices @ camera_from_face[:3, :3].T + position
                print('Camera-from-face matrix:', camera_from_face)
                print('Camera-relative vertices (m):', camera_vertices)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## Metric face vertices and triangle topology (USB)

Source: [face/03_metric_mesh_usb.py](../../examples/documentation/face/03_metric_mesh_usb.py)

```bash
python examples/documentation/face/03_metric_mesh_usb.py
```

```python
from asmagic import FaceDataSubscriber
from asmagic.geometry import pose_matrix
import numpy as np

IPHONE_IP = "usb"  # Use usb:DEVICE_UDID to select a specific iPhone.


def main():
    sub = FaceDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive()
            if not frame.has_face:
                print('No face in this frame')
                continue
            print('Flat triangle IDs:', frame.triangle_indices)
            vertices = frame.face_vertices
            if vertices is None or frame.tracking_mode != 'true_depth':
                print('Metric face mesh unavailable')
                continue
            row_by_id = {point.index: row for row, point in enumerate(frame.landmarks)}
            triangle_rows = np.array([
                [row_by_id[int(vertex)] for vertex in triangle]
                for triangle in frame.triangles
                if all(int(vertex) in row_by_id for vertex in triangle)
            ], dtype=np.int32).reshape(-1, 3)
            print('Vertices (m):', vertices)
            print('Triangle row indices:', triangle_rows)
            print('Triangle vertex coordinates (M x 3 x 3):', vertices[triangle_rows])
            position = frame.camera_position_meters
            orientation = frame.camera_orientation
            if position is not None and orientation is not None:
                # Face-local -> camera coordinates, in meters; no image mirroring.
                camera_from_face = pose_matrix(np.concatenate([position, orientation]))
                camera_vertices = vertices @ camera_from_face[:3, :3].T + position
                print('Camera-from-face matrix:', camera_from_face)
                print('Camera-relative vertices (m):', camera_vertices)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## Inspect every face field and its Python type (Network)

Source: [face/07_field_types.py](../../examples/documentation/face/07_field_types.py)

```bash
python examples/documentation/face/07_field_types.py
```

```python
from dataclasses import fields

import numpy as np
from asmagic import FaceDataSubscriber, FaceFrame

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.
FRAME_FIELDS = tuple(item.name for item in fields(FaceFrame)) + (
    'timestamp', 'blendshape_coefficients', 'points', 'triangles', 'face_vertices',
)


def describe(value):
    if isinstance(value, np.ndarray):
        return 'numpy.ndarray, dtype={}, shape={}'.format(value.dtype, value.shape)
    if isinstance(value, (dict, tuple)):
        return '{}; count={}'.format(type(value).__name__, len(value))
    return '{}: {}'.format(type(value).__name__, value)


def main():
    sub = FaceDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive(timeout=1000)
            if frame is None:
                print('No new frame within the timeout')
                continue
            print('Frame type:', type(frame).__name__)
            for name in FRAME_FIELDS:
                value = getattr(frame, name)
                if name == 'protobuf':
                    print(name, type(value).__name__, value.DESCRIPTOR.full_name)
                else:
                    print(name, describe(value))
            if frame.image_location is not None:
                for item in fields(frame.image_location):
                    print('image_location.' + item.name,
                          describe(getattr(frame.image_location, item.name)))
            if frame.landmarks:
                point = frame.landmarks[0]
                for item in fields(point):
                    print('landmarks[0].' + item.name,
                          describe(getattr(point, item.name)))
            if frame.blendshapes:
                name = next(iter(frame.blendshapes))
                print('Blendshape key:', describe(name))
                print('Blendshape value:', describe(frame.blendshapes[name]))
    except (KeyboardInterrupt, StopIteration):
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## Inspect every face field and its Python type (USB)

Source: [face/07_field_types_usb.py](../../examples/documentation/face/07_field_types_usb.py)

```bash
python examples/documentation/face/07_field_types_usb.py
```

```python
from dataclasses import fields

import numpy as np
from asmagic import FaceDataSubscriber, FaceFrame

IPHONE_IP = "usb"  # Use usb:DEVICE_UDID to select a specific iPhone.
FRAME_FIELDS = tuple(item.name for item in fields(FaceFrame)) + (
    'timestamp', 'blendshape_coefficients', 'points', 'triangles', 'face_vertices',
)


def describe(value):
    if isinstance(value, np.ndarray):
        return 'numpy.ndarray, dtype={}, shape={}'.format(value.dtype, value.shape)
    if isinstance(value, (dict, tuple)):
        return '{}; count={}'.format(type(value).__name__, len(value))
    return '{}: {}'.format(type(value).__name__, value)


def main():
    sub = FaceDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive(timeout=1000)
            if frame is None:
                print('No new frame within the timeout')
                continue
            print('Frame type:', type(frame).__name__)
            for name in FRAME_FIELDS:
                value = getattr(frame, name)
                if name == 'protobuf':
                    print(name, type(value).__name__, value.DESCRIPTOR.full_name)
                else:
                    print(name, describe(value))
            if frame.image_location is not None:
                for item in fields(frame.image_location):
                    print('image_location.' + item.name,
                          describe(getattr(frame.image_location, item.name)))
            if frame.landmarks:
                point = frame.landmarks[0]
                for item in fields(point):
                    print('landmarks[0].' + item.name,
                          describe(getattr(point, item.name)))
            if frame.blendshapes:
                name = next(iter(frame.blendshapes))
                print('Blendshape key:', describe(name))
                print('Blendshape value:', describe(frame.blendshapes[name]))
    except (KeyboardInterrupt, StopIteration):
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```
