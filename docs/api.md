# API reference

For standalone files whose complete code is also present in Markdown, see the [runnable documentation examples](examples/index.md) and [Data Format and API](examples/api-reference.md). Each example can be run independently, including skeleton display switches.

## Common ZeroMQ interface

All basic examples use `while True` with `receive()` and close the receiver in `finally`. `receive()` waits for a valid frame; `receive(timeout=...)` adds a bounded wait and returns `None` on timeout. Both modes raise `StopIteration` after closure. Watch uses the same receiving method for batches. AR and CameraDataSubscriber default to `hwm=32, conflate=False`, buffering up to 32 decoded frames.

`IMUDataSubscriber`, `JoystickDataSubscriber`, `AirPodsDataSubscriber`, `BodyPoseDataSubscriber`, `HandPoseDataSubscriber`, `FaceDataSubscriber`, and `ClawDataSubscriber` share:

`Subscriber(ip, port=DEFAULT_PORT, hwm=1, conflate=True, verbose=False)`

Body Tracking uses `BodyTrackingDataSubscriber(ip, *, model, port=None, hwm=1, conflate=True, verbose=False)`. Set `model="arkit"` or `model="mediapipe"` to match the App's recognition setting. The native ports are 8100 and 8104 respectively; both return `BodyTrackingFrame` containing all people in that frame.

`ip` accepts an IPv4/IPv6 literal or a hostname, without `tcp://`. IPv6 is bracketed internally. `port` is 1–65535, `hwm` is a positive message count. `conflate=True` keeps the newest one-part ZeroMQ message. Use one thread per subscriber; sockets are not shared between threads.

| API | Result / meaning |
|---|---|
| `receive()` | Wait for one valid frame; StopIteration when closed |
| `receive(timeout=1000)` | Wait up to 1000 milliseconds for valid data; `None` on timeout, StopIteration when closed |
| `for frame in sub` | Wait repeatedly until a frame arrives; stops after close |
| `stream(timeout=1000, on_frame=None, *, plot=False, plot_options=None)` | Generator; callback runs on the caller's thread before yielding; optional plotting for body/hand/face tracking |
| `Frame.protobuf` | The exact already-received message, including unknown fields |
| `Class.decode(payload)`; body: `BodyTrackingFrame.from_bytes(payload, model=...)` | Offline decode into a typed frame, no socket needed |
| `close()` | Close with zero linger; repeated close is safe |
| `with Subscriber(...) as sub` | Automatic close on exit |
| `address`, `ip`, `port` | Local subscription configuration |
| `is_connected` | Local subscription open; not proof of device availability |
| `has_received_data` | At least one valid frame has arrived |
| `received_frames` | Count of successfully parsed messages |
| `last_received_at` | Local monotonic receive time, or `None` before the first frame |
| `last_error` | Last decode error text; cleared by a valid frame |

Timeouts are integer **milliseconds**. `0` polls; `-1` or `None` waits indefinitely. Recoverable malformed packets are skipped within the same timeout budget; AR decode errors still raise `RuntimeError`. A received empty tracking frame is still a frame. Protobuf does not tag its root type, so an endpoint's schema must be selected correctly; a structurally compatible wrong message can parse without detecting a mismatch.

### Receiving frames

Call `receive()` once and read all fields on that frame.

AR matrix layouts, quaternion order and transform composition are specified in [AR Pose Format](examples/api-reference.md#ar-pose-format). `frame.depth` retains the original uint16 data. `frame.show_images()` displays both available images by default.

## Returned frames

| Type | Fields and helpers |
|---|---|
| `CameraFrame` | Camera-only RGB on 8105: `color_array`, `color_upright`, `color_bytes`, `has_color_image`, `rgb_width`, `rgb_height`, timestamps, frame ID and codec metadata; `show_color()` displays one image. `image` and `image_upright` remain aliases. [Guide](examples/camera.md) |
| `ARFrame` | Original timestamp/bytes/dimensions/pose/velocity/intrinsics; added frame/source time, RGB dimensions, depth confidence/scale, session IDs, shared-world flag and all RGB codec fields |
| `ARFrame` images | `has_color_image`, `has_depth_image`, `color_bytes`, `color_array` / `color`, `depth_array` / `depth`, `depth_confidence_array`, `rgb_codec_name` |
| `ARFrame` matrix properties (added) | `local_pose_matrix`, `global_pose_matrix` (4×4), `camera_intrinsics_matrix` (3×3); original `local_pose`, `global_pose`, `camera_intrinsics` stay unchanged |
| `ARFrame` pose/display | `has_pose`, `show_color(window_name="Color Image")`, `show_depth(window_name="Depth Image", colormap=None)`, `show_images(show_color=True, show_depth=True, color_window="Color Image", depth_window="Depth Image")` |
| `IMUFrame` | `timestamp`, `accelerometer`, `gyroscope`, `magnetometer`, `gravity`, `user_acceleration`, `attitude`; corresponding `has_*` flags. Received vectors retain their original 3/4-element zero fallback when a sensor is absent; `has_*` is false for that sensor |
| `JoystickFrame` | Original `timestamp`, `left_joystick`, `right_joystick`, `buttons`, `left_x/y`, `right_x/y`, `button1…4`, `has_*`; added `button` named controls, `left_stick` / `right_stick` aliases, optional structured sections, name, connection and battery |
| `AirPodsFrame` | `timestamp`, `rotation` (quaternion array `[qx, qy, qz, qw]`), `protobuf` |
| `BodyPoseFrame` | Optional raw `upper_body`, `json_data`, `detection_fps`, `frame_id`; `timestamp` is nested upper-body milliseconds |
| `BodyTrackingFrame` | Model, session/world IDs, timestamps, every person in `people`, ID lookup and optional selected person. See [full body definitions](body-tracking.md) |
| `JointTransform` | `position` (3-vector), `rotation` (x,y,z,w), `matrix` (4×4) |
| `BodyTrackingJoints` / `HandJoints` | Named optional attributes: `person.joints.left_wrist` and `hand.joints.wrist`; full dictionary access remains available |
| `HandPoseFrame` | `source_timestamp` / `timestamp`, image size/orientation, `unknown_hand_count`, optional `left` / `right` (aliases of `left_hand` / `right_hand`), `hands` tuple of assigned hands, `hand_count`, `has_left_hand`, `has_right_hand` |
| `Hand` | `side` (`HandSide.LEFT` / `RIGHT` / `UNKNOWN`), `confidence`, optional `wrist`, finger groups `thumb`, `index`, `middle`, `ring`, `little`; compatible `joints` dictionary, compact N×2 `points`, fixed-row `as_arrays()` |
| `HandFinger` / `HandThumb` | Non-thumb `.mcp`, `.pip`, `.dip`, `.tip`; thumb `.cmc`, `.mp`, `.ip`, `.tip`. Each is an optional `HandJoint` |
| `HandJoint` | `name`, `x`, `y`, `confidence`, `(x, y)` tuple `xy`, `to_pixels(image_width, image_height)` for continuous raw pixels |
| `FaceFrame` | `source_timestamp` / `timestamp`, `has_face`, image metadata/location, optional camera-relative pose, `blendshapes` / `blendshape_coefficients` dictionaries, `landmarks`, `triangle_indices`, mode, sequence, session, schema version, EXIF rotation |
| `FaceFrame` arrays | `points` N×2; `face_vertices` N×3 or `None`; `triangles` M×3 vertex IDs. Match triangle IDs to `FaceLandmark.index` when vertices have been filtered |
| `FaceLandmark` | `index`, `region`, `image_x`, `image_y`, optional `position_face_meters` |
| `FaceImageLocation` | `center_x`, `center_y`, `width`, `height` in raw normalized image coordinates |
| `ClawFrame` | `timestamp`, `angle`, optional raw `motor` (`angle`, `angle_percent`, `speed`, `iq`, `temperature`) |

Structured controller sections are generated Protobuf messages, with the same names as the schema: `face_buttons`, `dpad`, `shoulders`, `triggers`, `stick_buttons`, `system_buttons`, `motion`. Their presence is represented by `None` vs a message, even when an available section contains all zeros.

`FaceFrame.tracking_mode` is `"true_depth"`, `"vision"`, `"unspecified"`, or `"unknown"`. On old senders, unavailable new scalar metadata retains Protobuf defaults; the SDK does not infer a schema version from payload size.

## Watch HTTP interface

```text
WatchIMUReceiver(host="127.0.0.1", port=8002, conflate=True,
                 max_batches=32, payload_format="batch", verbose=False)
```

`host` is this computer's bind interface; use `"0.0.0.0"` for IPv4 devices on the local network. `port=0` chooses a free port for tests. Set the Watch's server IP/port to this computer's reachable address and `receiver.port`. Do not pass the Watch IP as the bind address.

`receive()` returns `WatchBatch`; `receive(timeout=...)` returns a batch or `None` on timeout, with the same timeout units and closure behavior as ZeroMQ. Iteration and `stream()` yield batches. `iter_samples(timeout=1000)` flattens complete received batches. The class also has `close()`, context manager, `decode(payload)` (instance method), `address`, `is_connected`, `has_received_data`, `received_frames`, `dropped_batches`, `last_received_at`, `last_error`. Legacy `get()` / `get_frame()` are retained for compatibility.

`WatchBatch.frames` is a tuple of `WatchFrame`; other fields are `batch_timestamp`, `frame_count`, `timestamp` alias and `protobuf`. `WatchFrame` has timestamp and NumPy arrays `attitude`, `rotation_rate`, `gravity`, `acceleration`, plus `protobuf`. `received_frames` counts batches; sum `len(batch.frames)` to count samples.

Default conflation discards earlier batches but preserves every sample in the chosen batch. With `conflate=False`, up to `max_batches` are queued; older batches drop when full. `close()` wakes pending `get(-1)` calls. The HTTP server accepts only the configured schema and rejects invalid requests, missing/invalid length, payloads over 1 MiB and mismatched frame counts.

## Raw and legacy APIs

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

`ProtobufSubscriber(ip, port, message_type, hwm=1, conflate=True, verbose=False)` returns fresh generated messages; `.decode(payload)` is an instance method. `MagiClawDataSubscriber(ip, port, ...)` returns the legacy combined message. `LegacyWatchDataSubscriber(ip, port, ...)` returns a `WatchFrame`; its old schema has no timestamp.

`asmagic.proto` contains generated modules for camera, IMU, joystick, AirPods, upper body, AR body, hand, face/hand, gripper, legacy combined devices, legacy Watch and Watch batches. Schemas use a private descriptor pool, so importing older standalone bindings such as `joystickmagic` does not collide with the extended controller schema.

## Body people, named joints and arrays

The required `model` argument selects ARKit or MediaPipe and its native port. Read one frame, then iterate `frame.people` or use `frame.person(id)`. Named joint access works for both models:

```python
from asmagic import BodyTrackingDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.
MODEL = "mediapipe"  # Match the App setting: "mediapipe" or "arkit".


def print_person_joints(person):
    print(f"\nPerson {person.label} (ID: {person.id})")
    # Read both sides of the upper body and legs by their anatomical names.
    named_joints = [
        ("Left shoulder", person.joints.left_shoulder),
        ("Right shoulder", person.joints.right_shoulder),
        ("Left elbow", person.joints.left_elbow),
        ("Right elbow", person.joints.right_elbow),
        ("Left wrist", person.joints.left_wrist),
        ("Right wrist", person.joints.right_wrist),
        ("Left hip", person.joints.left_hip),
        ("Right hip", person.joints.right_hip),
        ("Left knee", person.joints.left_knee),
        ("Right knee", person.joints.right_knee),
        ("Left ankle", person.joints.left_ankle),
        ("Right ankle", person.joints.right_ankle),
    ]
    for location, body_joint in named_joints:
        if body_joint is None:
            print(f"  {location}: joint unavailable")
            continue
        print(f"  {location}: body [x, y, z] (m)={body_joint.position}")
        print(f"  {location}: world [x, y, z] (m)={body_joint.world_position}")
        print(f"  {location}: rotation [qx, qy, qz, qw]={body_joint.rotation}")
        print(f"  {location}: usable={body_joint.usable}")


def main():
    sub = BodyTrackingDataSubscriber(IPHONE_IP, model=MODEL)
    try:
        while True:
            frame = sub.receive()
            print("\nPeople:", frame.person_count)
            if not frame.people:
                print("No person detected in this frame")
            for person in frame.people:
                print_person_joints(person)
    except (KeyboardInterrupt, StopIteration):
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

Native arrays retain every detector node. The common layout provides twelve fixed anatomical rows. Position and rotation validity are separate, and unavailable world coordinates stay missing. See the [illustrated body guide](body-tracking.md) for exact types, units, confidence and identity definitions.

```python
from asmagic import BodyTrackingDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.
MODEL = "mediapipe"  # Match the App setting: "mediapipe" or "arkit".


def main():
    sub = BodyTrackingDataSubscriber(IPHONE_IP, model=MODEL)
    try:
        while True:
            frame = sub.receive()
            if not frame.people:
                print("No person detected in this frame")
                continue
            for person in frame.people:
                # Omit layout="common" to read all 33 or 91 model-specific rows.
                body = person.skeleton(space="body", layout="common")
                world = person.skeleton(space="world", layout="common")
                print(f"\nPerson {person.label} (ID: {person.id})")
                print("Joint names:", body.names)
                print("Body positions [x, y, z] (m):\n", body.positions)
                print("Position available:", body.valid)
                print("Usable positions:", body.usable)
                print("Rotations [qx, qy, qz, qw]:\n", body.rotations)
                print("Rotation available:", body.rotation_valid)
                print("Available body positions only:\n", body.positions[body.valid])

                # A row identifies the same joint in the body and world arrays.
                for row, name in enumerate(body.names):
                    body_position = body.positions[row] if body.valid[row] else None
                    world_position = world.positions[row] if world.valid[row] else None
                    print(f"Row {row} ({name}): body={body_position}, "
                          f"world={world_position}")
    except (KeyboardInterrupt, StopIteration):
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

Hand Tracking has its own 21-joint named and bulk API:

```python
from asmagic import HandPoseDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def print_hand_pixels(side, hand, width, height):
    print(f"\n{side} hand:")
    if hand is None:
        print("  Not detected")
        return

    named_joints = [
        ("Wrist", hand.wrist),
        ("Thumb fingertip", hand.thumb.tip),
        ("Index fingertip", hand.index.tip),
        ("Middle fingertip", hand.middle.tip),
        ("Ring fingertip", hand.ring.tip),
        ("Little fingertip", hand.little.tip),
    ]
    for location, hand_joint in named_joints:
        if hand_joint is None:
            print(f"  {location}: not detected")
            continue
        print(f"  {location}: normalized (x, y)={hand_joint.xy}")
        if width > 0 and height > 0:
            print(f"  {location}: pixels (x, y)="
                  f"{hand_joint.to_pixels(width, height)}")


def main():
    sub = HandPoseDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive()
            width, height = frame.image_width, frame.image_height
            print("\nTime:", frame.timestamp)
            print("Image size (width, height):", (width, height))
            if width <= 0 or height <= 0:
                print("Image size unavailable; printing normalized coordinates only")
            print_hand_pixels("Left", frame.left, width, height)
            print_hand_pixels("Right", frame.right, width, height)
    except (KeyboardInterrupt, StopIteration):
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

`Hand.as_arrays()` returns `HandJointArrays(names, points, confidences, valid)`. Missing point and confidence rows are NaN. The first 21 rows follow the hand protocol joint order; unknown extension names are appended alphabetically. No mirroring, rotation or confidence filtering is applied. Absent hands remain `None` on both standalone and face/hand frames. The original `Hand.points` continues to return only received points in dictionary order; use `as_arrays()` for stable rows across frames. Exports are independent NumPy snapshots; request a new export after changing a frame's dictionaries.

## Optional tracking plots

Install `asmagic` (local checkout: `pip install -e .`). Matplotlib and PyAV are included in the default installation. Normal receiving and `enabled=False` do not import Matplotlib. Plotting uses the caller's main thread and a GUI backend; use Agg for saved images in a headless environment.

`BodyTrackingFrame`, `BodyPoseFrame`, `HandPoseFrame`, `FaceFrame` and `Hand` expose `plot(enabled=True, plotter=None, **options)`. The returned `TrackingPlotter` can be reused with `update(frame)` or `next_frame.plot(plotter=viewer)`; call `close()` at the end. Calling `plot()` on every frame without reusing it creates multiple windows. Disabled calls return `None`.

`TrackingPlotter(space=BodyCoordinateSpace.BODY, labels=False, max_fps=30, stale_after=2.0, min_confidence=0.0)` provides `update(frame, force=False)`, `idle()`, `is_open`, `save(path, **savefig_options)`, `close()` and context management. `idle()` handles window events and erases stale data during receive timeouts. A plotter accepts one frame type. BODY/WORLD are supported for 3D body plots; PARENT is rejected because its joint positions have different origins. Invalid/missing nodes are not connected or zero-filled. `max_fps` limits drawing, not source/receive rate or message identity. `min_confidence` filters hand visualization only.

`HandTrackingWindow(labels=True, max_fps=30, stale_after=2.0, min_confidence=0.0)` specializes this API for two anatomical hand panels, blue L and orange R, with joint names and row IDs. It opens before the first frame. `update(frame)` accepts a `HandPoseFrame`; `update(None)` pumps events during timeouts. Both return this window. It inherits `is_open`, `idle()`, `save()`, `close()` and context management. See the [complete hand window example](hands.md#可视化窗口-api).

Use `sub.stream(plot=True, plot_options={...})` for automatic lifecycle management on tracking subscribers. Its generator yields the same decoded frame it draws, never receives an extra frame to plot, and closes its window on generator close. Closing the window ends the generator. Use `contextlib.closing` when breaking early. Other streams reject `plot=True`; camera frames retain `show_images()`. Constructor signatures remain unchanged. See [complete examples and device testing](device-testing.md).

## Named joystick controls

`frame.button` returns `JoystickButtons`: named booleans such as `.square`, `.l1`, `.up` and `.home`, plus analog `.l2` / `.r2` values from 0.0 to 1.0. Original numbered button fields remain supported. See [all controls](joystick.md) and the [complete examples](examples/joystick.md).

The named factory also accepts `subscribe("body", ip, model="mediapipe")` or `model="arkit"`. `BodyTrackingDataSubscriber.decode(payload)` is an instance method using its configured model.
