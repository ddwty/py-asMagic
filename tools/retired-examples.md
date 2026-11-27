# Retired SDK example sources

Developer archive for the requested cleanup. Active user-run examples are the exact GitBook chapter copies in `examples/documentation/`. These earlier scripts are retained for provenance, not as a second set of supported examples.

Baseline: `c91e2387170e77e560782b4190f3ccebeac97c42`.

## examples/_common.py

```python
"""Shared command-line receive loop used by runnable examples."""
import argparse


def run(subscriber_type, describe, description, plotting=False):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("ip", help="Sender IP address or hostname")
    parser.add_argument("--port", type=int, help="Override the stream's default port")
    parser.add_argument("--count", type=int, default=0, help="Stop after this many frames; 0 runs until Ctrl-C")
    if plotting:
        parser.add_argument("--plot", action="store_true", help="Show tracking plot; off by default")
        parser.add_argument("--space", choices=("body", "world"), default="body", help="3D body coordinate space")
    args = parser.parse_args()
    options = {"port": args.port} if args.port is not None else {}
    sub = subscriber_type(args.ip, **options)
    viewer = None
    count = 0
    try:
        if plotting and args.plot:
            from asmagic import TrackingPlotter
            viewer = TrackingPlotter(space=args.space)
        while viewer is None or viewer.is_open:
            frame = sub.receive(timeout=50) if viewer is not None else sub.receive()
            if frame is None:
                if viewer is not None:
                    viewer.idle()
                continue
            if viewer is not None:
                if not viewer.is_open:
                    break
                viewer.update(frame)
            describe(frame)
            count += 1
            if args.count > 0 and count >= args.count:
                break
    except (KeyboardInterrupt, StopIteration):
        pass
    finally:
        if viewer is not None:
            viewer.close()
        sub.close()
```

## examples/camera_only.py

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

## examples/documentation/ar/01_continuous.py

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

## examples/documentation/ar/07_metadata.py

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

## examples/documentation/ar/08_frame_fields.py

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

## examples/documentation/ar/09_intrinsics.py

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

## examples/documentation/ar/10_selected_fields.py

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

## examples/documentation/ar/11_quick_start.py

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

## examples/documentation/ar/12_authored_continuous.py

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

## examples/documentation/claw/01_first_gripper.py

```python
from asmagic import ClawDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def main():
    sub = ClawDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive()
            print("Time:", frame.timestamp)
            print("Gripper command (%):", frame.angle)
            print("Motor:", frame.motor)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## examples/documentation/claw/02_second_gripper.py

```python
from asmagic import ClawDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def main():
    sub = ClawDataSubscriber(IPHONE_IP, port=5401)
    try:
        while True:
            frame = sub.receive()
            print("Time:", frame.timestamp)
            print("Gripper command (%):", frame.angle)
            print("Motor:", frame.motor)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## examples/documentation/common/01_options_timeout_and_cleanup.py

```python
from asmagic import ARDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def main():
    sub = ARDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive(timeout=1000)
            if frame is None:
                print("No frame within 1000 ms")
                continue
            print("Time:", frame.timestamp)
            print("Received frames:", sub.received_frames)
            print("Last received:", sub.last_received_at)
            print("Last error:", sub.last_error)
            print("Local pose:", frame.local_pose)
    except (KeyboardInterrupt, StopIteration):
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## examples/documentation/common/02_stream_callback.py

```python
from asmagic import IMUDataSubscriber

IPHONE_IP = "192.168.1.100"


def on_frame(frame):
    print(frame.timestamp, frame.gyroscope)


def main():
    sub = IMUDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive()
            on_frame(frame)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## examples/documentation/common/03_named_stream_factory.py

```python
from asmagic import STREAMS, subscribe

IPHONE_IP = "192.168.1.100"
STREAM_NAME = "hand"


def main():
    for name, info in STREAMS.items():
        print(name, info.subscriber.__name__, info.port, info.message, info.feature)
    sub = subscribe(STREAM_NAME, IPHONE_IP, verbose=True)
    try:
        while True:
            frame = sub.receive()
            print(type(frame).__name__, frame.timestamp)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## examples/documentation/common/04_raw_protobuf.py

```python
from asmagic import ClawDataSubscriber, ProtobufSubscriber
from asmagic.proto import claw_msg_pb2

IPHONE_IP = "192.168.1.100"
USE_TYPED_SUBSCRIBER = True


def main():
    if USE_TYPED_SUBSCRIBER:
        sub = ClawDataSubscriber(IPHONE_IP, port=5301)
    else:
        sub = ProtobufSubscriber(IPHONE_IP, 5301, claw_msg_pb2.Claw)
    try:
        while True:
            frame = sub.receive()
            message = frame.protobuf if USE_TYPED_SUBSCRIBER else frame
            print('Schema:', message.DESCRIPTOR.full_name)
            print('Message:', message)
            if message.HasField('motor'):
                print('Motor percent:', message.motor.angle_percent)
            if not USE_TYPED_SUBSCRIBER:
                decoded = sub.decode(message.SerializeToString())
                print('Decoded without receiving another frame:', decoded)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## examples/documentation/common/05_save_protobuf_frame.py

```python
from pathlib import Path
from asmagic import ARDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.
OUTPUT = Path("reports/manual-ar-frame.bin")


def main():
    sub = ARDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive()
            OUTPUT.parent.mkdir(parents=True, exist_ok=True)
            OUTPUT.write_bytes(frame.protobuf.SerializeToString())
            print("Saved:", OUTPUT)
            break
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## examples/documentation/common/06_decode_saved_frame.py

```python
from pathlib import Path
from asmagic import ARDataSubscriber

INPUT = Path("reports/manual-ar-frame.bin")


def main():
    if not INPUT.is_file():
        print("First run common/05_save_protobuf_frame.py to create", INPUT)
        return
    frame = ARDataSubscriber.decode(INPUT.read_bytes())
    print("Timestamp:", frame.timestamp)
    print("Local pose:", frame.local_pose)
    print("RGB:", frame.color_array)
    print("Depth:", frame.depth)
    print("Depth size:", frame.depth_width, frame.depth_height)


if __name__ == "__main__":
    main()
```

## examples/documentation/common/07_receive_loop.py

```python
from asmagic import IMUDataSubscriber

sub = IMUDataSubscriber("192.168.1.100")  # Replace with your iPhone's IP.

try:
    while True:
        frame = sub.receive()
        print(frame.timestamp, frame.gyroscope)
except KeyboardInterrupt:
    pass
finally:
    sub.close()
```

## examples/documentation/face/05_optional_plot.py

```python
from asmagic import TrackingPlotter
from asmagic import FaceDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.
SHOW_SKELETON = True


def main():
    sub = FaceDataSubscriber(IPHONE_IP)
    viewer = TrackingPlotter() if SHOW_SKELETON else None
    try:
        while True:
            frame = sub.receive()
            if viewer is not None:
                if not viewer.is_open:
                    break
                viewer.update(frame)
            print("Time:", frame.timestamp)
            print("Face points:", frame.points)
    except KeyboardInterrupt:
        pass
    finally:
        if viewer is not None:
            viewer.close()
        sub.close()


if __name__ == "__main__":
    main()
```

## examples/documentation/face/06_face_and_hands.py

```python
from asmagic import HandPoseDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def main():
    sub = HandPoseDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive()
            print("Time:", frame.timestamp)
            print("Hand count:", frame.hand_count)
            print("Left hand:", frame.left_hand)
            print("Right hand:", frame.right_hand)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## examples/documentation/legacy/01_magiclaw_combined.py

```python
from asmagic import MagiClawDataSubscriber

IPHONE_IP = "192.168.1.100"


def main():
    sub = None
    try:
        port = int(input("Enter your legacy MagiClaw publisher's TCP port: "))
        sub = MagiClawDataSubscriber(IPHONE_IP, port=port)
        while True:
            message = sub.receive()
            print('Timestamp:', message.timestamp)
            for name in ('claw', 'finger_0', 'finger_1', 'phone'):
                if message.HasField(name):
                    print(name, getattr(message, name))
    except KeyboardInterrupt:
        pass
    finally:
        if sub is not None:
            sub.close()


if __name__ == "__main__":
    main()
```

## examples/documentation/legacy/02_watch_zmq.py

```python
from asmagic import LegacyWatchDataSubscriber

IPHONE_IP = "192.168.1.100"


def main():
    sub = None
    try:
        port = int(input("Enter your legacy Watch publisher's TCP port: "))
        sub = LegacyWatchDataSubscriber(IPHONE_IP, port=port)
        while True:
            frame = sub.receive()
            print(frame.timestamp, frame.attitude, frame.rotation_rate, frame.gravity, frame.acceleration)
            offline = LegacyWatchDataSubscriber.decode(frame.protobuf.SerializeToString())
            print('Offline decoded attitude:', offline.attitude)
    except KeyboardInterrupt:
        pass
    finally:
        if sub is not None:
            sub.close()


if __name__ == "__main__":
    main()
```

## examples/documentation/plotting/01_manual_plotter.py

```python
from asmagic import BodyTrackingDataSubscriber, TrackingPlotter

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.
MODEL = "mediapipe"  # Match the App setting: "mediapipe" or "arkit".
SHOW_SKELETON = True


def main():
    sub = BodyTrackingDataSubscriber(IPHONE_IP, model=MODEL)
    viewer = TrackingPlotter() if SHOW_SKELETON else None
    try:
        while viewer is None or viewer.is_open:
            frame = sub.receive(timeout=50 if viewer is not None else 1000)
            if frame is None:
                if viewer is not None:
                    viewer.idle()
                continue
            if viewer is not None:
                viewer.update(frame)
            print("Time:", frame.timestamp)
            for person in frame.people:
                print("Person:", person.id, "Positions (m):", person.skeleton().positions)
    except KeyboardInterrupt:
        pass
    finally:
        if viewer is not None:
            viewer.close()
        sub.close()


if __name__ == "__main__":
    main()
```

## examples/documentation/plotting/02_frame_plot.py

```python
from asmagic import TrackingPlotter
from asmagic import HandPoseDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.
SHOW_SKELETON = True


def main():
    sub = HandPoseDataSubscriber(IPHONE_IP)
    viewer = TrackingPlotter() if SHOW_SKELETON else None
    try:
        while True:
            frame = sub.receive()
            if viewer is not None:
                if not viewer.is_open:
                    break
                viewer.update(frame)
            print("Time:", frame.timestamp)
            print("Hand count:", frame.hand_count)
    except KeyboardInterrupt:
        pass
    finally:
        if viewer is not None:
            viewer.close()
        sub.close()


if __name__ == "__main__":
    main()
```

## examples/documentation/plotting/03_single_hand.py

```python
from asmagic import TrackingPlotter
from asmagic import HandPoseDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def main():
    sub = HandPoseDataSubscriber(IPHONE_IP)
    viewer = TrackingPlotter()
    try:
        while True:
            frame = sub.receive()
            hand = frame.left_hand
            if hand is not None:
                viewer.update(hand)
                print("Time:", frame.timestamp)
                print("Left hand points:", hand.as_arrays().points)
            else:
                viewer.idle()
            if not viewer.is_open:
                break
    except KeyboardInterrupt:
        pass
    finally:
        viewer.close()
        sub.close()


if __name__ == "__main__":
    main()
```

## examples/documentation/plotting/04_save_without_window.py

```python
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
from asmagic import BodyTrackingDataSubscriber, TrackingPlotter

IPHONE_IP = "192.168.1.100"
MODEL = "mediapipe"  # Match the App setting: "mediapipe" or "arkit".
OUTPUT = Path("reports/manual-body.png")


def main():
    sub = BodyTrackingDataSubscriber(IPHONE_IP, model=MODEL)
    viewer = TrackingPlotter(labels=True)
    try:
        while True:
            frame = sub.receive()
            if not any(person.skeleton().valid.any() for person in frame.people):
                print('Waiting for body positions')
                continue
            viewer.update(frame, force=True)
            viewer.figure.suptitle('Body tracking snapshot')
            viewer.axes[0].set_title('Session: ' + frame.session_id)
            OUTPUT.parent.mkdir(parents=True, exist_ok=True)
            viewer.save(OUTPUT, dpi=150, bbox_inches='tight')
            print('Saved:', OUTPUT.resolve())
            break
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()
        viewer.close()


if __name__ == "__main__":
    main()
```

## examples/documentation/upper_body/02_optional_skeleton.py

```python
from asmagic import TrackingPlotter
from asmagic import BodyPoseDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.
SHOW_SKELETON = True


def main():
    sub = BodyPoseDataSubscriber(IPHONE_IP)
    viewer = TrackingPlotter() if SHOW_SKELETON else None
    try:
        while True:
            frame = sub.receive()
            if viewer is not None:
                if not viewer.is_open:
                    break
                viewer.update(frame)
            print("Time:", frame.timestamp)
            print("Upper body:", frame.upper_body)
    except KeyboardInterrupt:
        pass
    finally:
        if viewer is not None:
            viewer.close()
        sub.close()


if __name__ == "__main__":
    main()
```

## examples/documentation/watch/01_batches.py

```python
from asmagic import WatchIMUReceiver



def main():
    sub = WatchIMUReceiver(host="0.0.0.0")
    try:
        while True:
            frame = sub.receive()
            for sample in frame.frames:
                print("Time:", sample.timestamp)
                print("Attitude:", sample.attitude)
                print("Rotation rate (rad/s):", sample.rotation_rate)
                print("Gravity (G):", sample.gravity)
                print("Acceleration (G):", sample.acceleration)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## examples/documentation/watch/02_individual_samples.py

```python
from asmagic import WatchIMUReceiver



def main():
    sub = WatchIMUReceiver(host="0.0.0.0")
    try:
        while True:
            frame = sub.receive()
            for sample in frame.frames:
                print("Time:", sample.timestamp)
                print("Attitude:", sample.attitude)
                print("Rotation rate (rad/s):", sample.rotation_rate)
                print("Gravity (G):", sample.gravity)
                print("Acceleration (G):", sample.acceleration)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## examples/documentation/watch/03_receive_methods.py

```python
from asmagic import WatchIMUReceiver



def main():
    sub = WatchIMUReceiver(host="0.0.0.0")
    try:
        while True:
            frame = sub.receive()
            for sample in frame.frames:
                print("Time:", sample.timestamp)
                print("Attitude:", sample.attitude)
                print("Rotation rate (rad/s):", sample.rotation_rate)
                print("Gravity (G):", sample.gravity)
                print("Acceleration (G):", sample.acceleration)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## examples/documentation/watch/04_payload_format_and_decode.py

```python
from asmagic import WatchIMUReceiver

PAYLOAD_FORMAT = "batch"  # "batch", "single" or "legacy".


def main():
    sub = WatchIMUReceiver(host="0.0.0.0", payload_format=PAYLOAD_FORMAT)
    try:
        while True:
            frame = sub.receive()
            message = frame.protobuf
            decoded = sub.decode(message.SerializeToString())
            print("Batch time:", decoded.timestamp)
            print("Samples:", decoded.frames)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## examples/preview_tracking_plots.py

```python
"""Export explicitly synthetic plot previews; this does not connect to the App."""
import argparse
from pathlib import Path

from asmagic import ARBodyDataSubscriber, HandPoseDataSubscriber, TrackingPlotter, HAND_JOINT_NAMES
from asmagic.proto import armpose_msg_pb2, hand_pose_pb2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="reports", help="Output PNG directory")
    args = parser.parse_args()
    import matplotlib
    matplotlib.use("Agg")
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    message = armpose_msg_pb2.Armpose(tracking_state="tracking", session_id="synthetic-preview")
    joints = {
        "hips_joint": ((0, 0, 0), None), "spine_3_joint": ((0, .28, 0), "hips_joint"),
        "spine_7_joint": ((0, .59, 0), "spine_3_joint"), "neck_1_joint": ((0, .72, 0), "spine_7_joint"),
        "head_joint": ((0, .92, 0), "neck_1_joint"),
        "left_shoulder_1_joint": ((-.18, .59, 0), "spine_7_joint"),
        "left_arm_joint": ((-.23, .58, 0), "left_shoulder_1_joint"),
        "left_forearm_joint": ((-.45, .35, .03), "left_arm_joint"),
        "left_hand_joint": ((-.59, .50, .08), "left_forearm_joint"),
        "right_shoulder_1_joint": ((.18, .59, 0), "spine_7_joint"),
        "right_arm_joint": ((.23, .58, 0), "right_shoulder_1_joint"),
        "right_forearm_joint": ((.46, .35, .02), "right_arm_joint"),
        "right_hand_joint": ((.54, .14, .06), "right_forearm_joint"),
        "left_upLeg_joint": ((-.12, -.08, 0), "hips_joint"),
        "left_leg_joint": ((-.14, -.49, .02), "left_upLeg_joint"),
        "left_foot_joint": ((-.14, -.9, 0), "left_leg_joint"),
        "left_toes_joint": ((-.14, -.93, .14), "left_foot_joint"),
        "right_upLeg_joint": ((.12, -.08, 0), "hips_joint"),
        "right_leg_joint": ((.14, -.49, .01), "right_upLeg_joint"),
        "right_foot_joint": ((.14, -.9, 0), "right_leg_joint"),
        "right_toes_joint": ((.14, -.93, .14), "right_foot_joint"),
    }
    for name, (position, parent) in joints.items():
        joint = message.joints[name]
        joint.position.x, joint.position.y, joint.position.z = position
        joint.rotation.w = 1
        message.tracked_joints[name] = name not in ("spine_3_joint", "left_toes_joint", "right_toes_joint")
        if parent:
            message.joint_parents[name] = parent
    body = ARBodyDataSubscriber.decode(message.SerializeToString())
    with TrackingPlotter() as plot:
        plot.update(body)
        plot.figure.suptitle("Synthetic fixture - not a device capture", fontsize=10)
        plot.save(output / "body-preview.png", dpi=150)

    message = hand_pose_pb2.HandPoseFrame(source_timestamp=1, image_width=1920, image_height=1080)
    points = [(.45, .85), (.34, .75), (.23, .65), (.14, .58), (.09, .51),
              (.37, .59), (.34, .4), (.33, .27), (.32, .16),
              (.49, .55), (.49, .32), (.49, .18), (.49, .08),
              (.60, .58), (.63, .36), (.65, .23), (.67, .14),
              (.70, .64), (.78, .49), (.83, .38), (.87, .30)]
    for side, hand in (("left", message.left_hand), ("right", message.right_hand)):
        hand.confidence = .95
        for name, (x, y) in zip(HAND_JOINT_NAMES, points):
            hand.joints.add(name=name, x=x if side == "left" else 1 - x, y=y, confidence=.95)
    with TrackingPlotter() as plot:
        plot.update(HandPoseDataSubscriber.decode(message.SerializeToString()))
        plot.figure.suptitle("Synthetic fixture - not a device capture", fontsize=10)
        plot.save(output / "hands-preview.png", dpi=150)
    print((output / "body-preview.png").resolve())
    print((output / "hands-preview.png").resolve())


if __name__ == "__main__":
    main()
```

## examples/read_airpods_data.py

```python
"""Run: python examples/read_airpods_data.py IPHONE_IP"""
from asmagic import AirPodsDataSubscriber
from _common import run


def describe(frame):
    print("Time:", frame.timestamp)
    print("Rotation:", frame.rotation)


if __name__ == "__main__":
    run(AirPodsDataSubscriber, describe, "Receive AirPodsData data")
```

## examples/read_ar_data.py

```python
"""Run: python examples/read_ar_data.py IPHONE_IP"""
from asmagic import ARDataSubscriber
from _common import run

def describe(frame):
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

if __name__ == "__main__":
    run(ARDataSubscriber, describe, "Receive ARData data")
```

## examples/read_body_data.py

```python
"""Run: python examples/read_body_data.py IPHONE_IP --model mediapipe [--plot]"""
import argparse
from asmagic import BodyTrackingDataSubscriber, TrackingPlotter


def describe(frame):
    print("Time:", frame.timestamp)
    print("Tracking:", frame.tracking_state)
    print("People:", frame.person_count)
    for person in frame.people:
        body = person.skeleton()
        print("Person:", person.id)
        print("Joint names:", body.names)
        print("Positions (m):", body.positions)
        print("Valid positions:", body.valid)
        print("Rotations:", body.rotations)
        print("Valid rotations:", body.rotation_valid)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ip", help="iPhone hostname or IP")
    parser.add_argument("--model", choices=("arkit", "mediapipe"), default="mediapipe",
                        help="Match the recognition model selected in the App")
    parser.add_argument("--plot", action="store_true")
    parser.add_argument("--space", choices=("body", "world"), default="body")
    args = parser.parse_args()
    sub = BodyTrackingDataSubscriber(args.ip, model=args.model)
    viewer = TrackingPlotter(space=args.space) if args.plot else None
    try:
        while viewer is None or viewer.is_open:
            frame = sub.receive(timeout=50 if viewer is not None else 1000)
            if frame is None:
                if viewer is not None:
                    viewer.idle()
                continue
            describe(frame)
            if viewer is not None:
                viewer.update(frame)
    except (KeyboardInterrupt, StopIteration):
        pass
    finally:
        sub.close()
        if viewer is not None:
            viewer.close()


if __name__ == "__main__":
    main()
```

## examples/read_claw_data.py

```python
"""Run: python examples/read_claw_data.py IPHONE_IP"""
from asmagic import ClawDataSubscriber
from _common import run


def describe(frame):
    print("Time:", frame.timestamp)
    print("Gripper command (%):", frame.angle)
    print("Motor:", frame.motor)


if __name__ == "__main__":
    run(ClawDataSubscriber, describe, "Receive ClawData data")
```

## examples/read_face_data.py

```python
"""Run: python examples/read_face_data.py IPHONE_IP"""
from asmagic import FaceDataSubscriber
from _common import run


def describe(frame):
    print("Time:", frame.timestamp)
    print("Face detected:", frame.has_face)
    print("Face points:", frame.points)
    print("Expressions:", frame.blendshapes)
    print("Position (m):", frame.camera_position_meters)
    print("Orientation:", frame.camera_orientation)


if __name__ == "__main__":
    run(FaceDataSubscriber, describe, "Receive FaceData data", plotting=True)
```

## examples/read_face_hand_data.py

```python
"""Run with --channel face or --channel hand; use separate terminals for both."""
import argparse
from asmagic import FaceDataSubscriber, HandPoseDataSubscriber


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ip", help="iPhone IP address")
    parser.add_argument("--channel", choices=("face", "hand"), default="face")
    args = parser.parse_args()
    subscriber_type = FaceDataSubscriber if args.channel == "face" else HandPoseDataSubscriber
    sub = subscriber_type(args.ip)
    try:
        while True:
            frame = sub.receive()
            print("Time:", frame.timestamp)
            if args.channel == "face":
                print("Face detected:", frame.has_face)
                print("Face points:", frame.points)
                print("Expressions:", frame.blendshapes)
            else:
                print("Hand count:", frame.hand_count)
                print("Left hand:", frame.left_hand)
                print("Right hand:", frame.right_hand)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## examples/read_hand_data.py

```python
"""Run: python examples/read_hand_data.py IPHONE_IP"""
from asmagic import HandPoseDataSubscriber
from _common import run


def describe(frame):
    print("Time:", frame.timestamp)
    print("Hand count:", frame.hand_count)
    print("Left hand:", frame.left_hand)
    print("Right hand:", frame.right_hand)


if __name__ == "__main__":
    run(HandPoseDataSubscriber, describe, "Receive HandPoseData data", plotting=True)
```

## examples/read_imu_data.py

```python
"""Run: python examples/read_imu_data.py IPHONE_IP"""
from asmagic import IMUDataSubscriber
from _common import run


def describe(frame):
    print("Time:", frame.timestamp)
    print("Accelerometer (G):", frame.accelerometer)
    print("Gyroscope (rad/s):", frame.gyroscope)
    print("Magnetometer (μT):", frame.magnetometer)
    print("Gravity (G):", frame.gravity)
    print("User acceleration (G):", frame.user_acceleration)
    print("Attitude:", frame.attitude)


if __name__ == "__main__":
    run(IMUDataSubscriber, describe, "Receive IMUData data")
```

## examples/read_joystick_data.py

```python
"""Run: python examples/read_joystick_data.py IPHONE_IP"""
from asmagic import JoystickDataSubscriber
from _common import run


def describe(data):
    print("Time:", data.timestamp)
    print("Left joystick:", data.left_x, data.left_y)
    print("Right joystick:", data.right_x, data.right_y)
    print("Triangle:", data.button.triangle)
    print("Square:", data.button.square)
    print("Cross:", data.button.cross)
    print("Circle:", data.button.circle)
    print("L1/R1:", data.button.l1, data.button.r1)
    print("L2/R2:", data.button.l2, data.button.r2)
    print("L3/R3:", data.button.l3, data.button.r3)
    print("D-pad up/down:", data.button.up, data.button.down)
    print("D-pad left/right:", data.button.left, data.button.right)
    print("Share/Options:", data.button.share, data.button.options)
    print("Home/Touchpad:", data.button.home, data.button.touchpad)
    print("Controller:", data.controller_name)
    print("Connected:", data.is_connected)
    print("Battery:", data.battery_level)
    print("Charging:", data.is_charging)
    if data.has_motion:
        print("Gravity (G):", data.gravity)
        print("Acceleration (G):", data.user_acceleration)
        print("Rotation rate (rad/s):", data.rotation_rate)
        print("Attitude:", data.attitude)


if __name__ == "__main__":
    run(JoystickDataSubscriber, describe, "Receive joystick input")
```

## examples/read_upper_body_data.py

```python
"""Run: python examples/read_upper_body_data.py IPHONE_IP"""
from asmagic import BodyPoseDataSubscriber
from _common import run


def describe(frame):
    print("Time:", frame.timestamp)
    print("Upper body:", frame.upper_body)
    print("Detection FPS:", frame.detection_fps)


if __name__ == "__main__":
    run(BodyPoseDataSubscriber, describe, "Receive BodyPoseData data", plotting=True)
```

## examples/receive_stream.py

```python
"""Receive any known ZeroMQ stream. Use --help for stream names and options."""
import argparse
from asmagic import STREAMS, subscribe


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stream", choices=sorted(STREAMS))
    parser.add_argument("ip", help="Sender IP address")
    parser.add_argument("--port", type=int)
    parser.add_argument("--count", type=int, default=0)
    args = parser.parse_args()
    options = {"port": args.port} if args.port is not None else {}
    sub = subscribe(args.stream, args.ip, **options)
    count = 0
    try:
        while True:
            frame = sub.receive()
            print("Frame:", frame)
            count += 1
            if args.count > 0 and count >= args.count:
                break
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## examples/receive_watch.py

```python
"""Listen for Watch HTTP protobuf batches; configure the Watch with this computer's IP."""
import argparse
from asmagic import WatchIMUReceiver


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1", help="Bind interface; use 0.0.0.0 for local-network senders")
    parser.add_argument("--port", type=int, default=8002)
    parser.add_argument("--all-batches", action="store_true", help="Queue up to 32 batches instead of conflating")
    parser.add_argument("--format", choices=["batch", "single", "legacy"], default="batch")
    args = parser.parse_args()
    sub = WatchIMUReceiver(args.host, args.port, conflate=not args.all_batches, payload_format=args.format)
    try:
        print("Listening on", sub.address)
        while True:
            frame = sub.receive()
            for sample in frame.frames:
                print("Time:", sample.timestamp)
                print("Attitude:", sample.attitude)
                print("Rotation rate (rad/s):", sample.rotation_rate)
                print("Gravity (G):", sample.gravity)
                print("Acceleration (G):", sample.acceleration)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## examples/simple_continuous.py

```python
"""Continuously receive camera pose. Run: python examples/simple_continuous.py SENDER_IP"""
from asmagic import ARDataSubscriber
from _common import run


def describe(frame):
    print("Time:", frame.timestamp)
    print("Local pose:", frame.local_pose)
    print("Velocity:", frame.velocity)


if __name__ == "__main__":
    run(ARDataSubscriber, describe, 'Continuously receive camera pose')
```

## examples/simple_with_images.py

```python
"""Camera display entrypoint; shares the documented preview example."""
import argparse
from importlib import import_module

main = import_module("documentation.ar.03_display_images").main


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ip", nargs="?", default="192.168.1.100")
    main(parser.parse_args().ip)
```

## examples/test_app_streams.py

```python
"""Real-device tests. Run --list, or --all --ip PHONE_IP --plot in a terminal."""
from asmagic.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
```

## examples/test_camera.py

```python
"""Camera display entrypoint; shares the documented preview example."""
import argparse
from importlib import import_module

main = import_module("documentation.ar.03_display_images").main


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ip", nargs="?", default="192.168.1.100")
    main(parser.parse_args().ip)
```

## examples/usb_imu.py

```python
"""Receive USB IMU data: python examples/usb_imu.py. Start IMU in the app."""
import asmagic


def main():
    with asmagic.IMUDataSubscriber("usb") as sub:
        while True:
            frame = sub.receive(timeout=1000)
            if frame is None:
                print(sub.last_error or "Waiting for iPhone IMU; open asMagic and start IMU streaming.")
            else:
                print(frame.timestamp, frame.accelerometer, frame.gyroscope)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
```
