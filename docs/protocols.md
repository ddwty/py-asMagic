# Wire protocol and ports

Protocol snapshots are included in `asmagic/proto/schemas/`; their SHA-256 hashes and origins are recorded in `asmagic/proto/schema_sources.json`. Each ZeroMQ output publishes a single Protobuf payload with no topic header. Receivers subscribe with an empty subscription filter; do not add multipart framing.

## Active outputs

| Stream | Transport / port | Root message | Python API |
|---|---|---|---|
| Camera only | ZeroMQ TCP 8105 | `Phone.Phone` (RGB fields only) | `CameraDataSubscriber` |
| Camera / pose | ZeroMQ TCP 8000 | `Phone.Phone` | `ARDataSubscriber` |
| AirPods | ZeroMQ TCP 8001 | `Airpods.Airpods` | `AirPodsDataSubscriber` |
| iPhone IMU | ZeroMQ TCP 8002 | `Imu.Imu` | `IMUDataSubscriber` |
| Vision upper body | ZeroMQ TCP 8010 | `BodyPose.BodyPoseMessage` | `BodyPoseDataSubscriber` |
| Controller | ZeroMQ TCP 8020 | `Joystick.Joystick` | `JoystickDataSubscriber` |
| ARKit body | ZeroMQ TCP 8100 | `Armpose.Armpose` | `BodyTrackingDataSubscriber(model="arkit")` |
| MediaPipe bodies | ZeroMQ TCP 8104 | `asmagic.body.v1.MultiPersonPoseFrame` | `BodyTrackingDataSubscriber(model="mediapipe")` |
| Hands from Stream or Face and Hand Tracking | ZeroMQ TCP 8101 | `Phone.HandPoseFrame` | `HandPoseDataSubscriber` |
| Face only | ZeroMQ TCP 8102 | `Phone.FaceTrackingFrame` | `FaceDataSubscriber` |
| Gripper | ZeroMQ TCP 5301 / 5401 | `Claw.Claw` | `ClawDataSubscriber` |
| Watch batch | HTTP POST to receiver, configurable port (default 8002), `/imu` | `watch_batch.WatchBatch` | `WatchIMUReceiver` |

Every feature starts its own output; opening an unrelated feature will not activate all ports. AR camera, AR body, and front-camera face tracking can require different camera sessions. A Python receiver does not require the Mac app's DeviceSession pairing.

`MagiClaw.MagiClaw` and `Watch.Watch` are included for legacy compatibility and have no assigned current app ZeroMQ port. Their subscribers require an explicit port. Generic `ProtobufSubscriber(ip, port, message_type)` handles any explicitly selected additional schema. JSON, Face Follow's legacy UDP packet/video/depth framing, robot RTDE/URScript, Bonjour pairing, and multipeer control messages are separate protocols, not Protobuf messages on these ZeroMQ ports.

## Ordinary camera RGB

Stream > Camera > Send camera uses an AVFoundation capture session and TCP 8105. The image is carried by the
existing Phone fields: timestamp, source_timestamp, frame_id, color_img, rgb_width/rgb_height,
image_rotation_quarter_turns_clockwise and RGB codec metadata. Pose, depth, intrinsics and AR-session
identifiers remain absent. source_timestamp is the camera sample presentation time in seconds.
The current sender physically applies preview orientation and front-camera mirroring, with zero rotation metadata.
Switching lenses or resolution starts a new encoder and resets frame numbering to 1.
`CameraDataSubscriber` shares the JPEG/HEVC receiver path and returns a CameraFrame with image-only fields.

## AR camera

Fields 1–9 remain wire compatible, including the misspelled wire name `camersIntrinsics`. Python exposes `camera_intrinsics` as before. Fields 10–24 add frame identity, source time, image sizes, depth confidence/scale, sessions, shared-world status and RGB codec information. There is no field 12 in the current schema; the receiver does not infer a missing field.

- `timestamp`: legacy sender wall-clock seconds. `source_timestamp`: ARKit monotonic seconds, not UTC. Do not subtract the receiver's clock to claim one-way latency. `frame_id` identifies a spatial frame.
- Current `local_pose` / `global_pose`: `[tx, ty, tz, qx, qy, qz, qw]`, translation in meters. Pose coordinates may be converted by the app's configured coordinate mode. The stream does not provide an explicit coordinate-mode field; do not assume one mode for all senders.
- `camera_intrinsics`: nine Float values in column order. `camera_intrinsics_matrix` reshapes them into a 3×3 matrix using Fortran order. Intrinsics describe the raw encoded RGB pixel orientation; display rotation does not modify them.
- `global_pose` can fall back to the local pose. It is a shared-world pose only when `global_pose_is_shared` is true and a shared-world ID is present. Session origins can change after restart.
- `depth_img`: little-endian UInt16, row-major, exactly `width × height × 2` bytes. Use `depth_meters_per_unit`; old frames with no scale use 0.0001. Zero is invalid/no depth. Confidence has one UInt8 ARConfidenceLevel per pixel (0 low, 1 medium, 2 high).
- `rgb_codec=0` or `1`: JPEG, preserving older senders. `rgb_codec=2`: HEVC with length-prefixed NAL units. `rgb_codec_config` carries VPS/SPS/PPS NAL units; `rgb_nal_unit_header_length` normally equals 4. HEVC can contain dependent frames. The receiver decodes every packet in sequence before replacing pending preview output, and waits for a keyframe after a reference reset. Python builds Annex B and uses PyAV, installed with the SDK by default, to decode; it does not send HEVC bytes to Pillow.

## Face and hands

**Hand-only contract:** Stream and Face and Hand Tracking both publish `Phone.HandPoseFrame` from `hand_pose.proto` on TCP **8101**, using the same `HandPoseStreamSender` / `HandPoseProtobufEncoder`. Both use `HandPoseDataSubscriber(ip)` or `subscribe("hand", ip)` with identical return types, fields and coordinate conventions. See [hand examples](examples/hand.md).

**Face-only contract:** Face and Hand Tracking publishes `Phone.FaceTrackingFrame` on **8102** using `FaceTrackingStreamSender`, decoded by `FaceDataSubscriber` / `subscribe("face", ip)`. Face tracking / Send face and Hand tracking / Send hands control recognition and output independently. Stopping or failing one output does not close the other. Disabling Face tracking switches TrueDepth capture to ordinary AVFoundation capture; disabling Hand tracking stops Vision hand inference. Leaving the page stops both.

The new face message uses schema version **2**. Face field numbers 1–9 and 11–17 remain unchanged; field 10 and the name `hand_pose` are reserved. There is no hand field in the current face root message. The old `Phone.FaceAndHandTrackingFrame` definition and SDK decoder are retained only for legacy packet compatibility. Current App sends no combined output. See [face examples](examples/face.md), [hand examples](examples/hand.md) and [migration notes](compatibility.md#independent-face-and-hand-outputs).

- A tracked TrueDepth face has all 52 named ARKit movement coefficients (0–1); a channel missing from ARKit's dictionary is encoded as zero. They are not emotion categories. Vision face tracking has no coefficient or metric-pose guarantee.
- `has_face=False` represents face loss. It does not mean the capture backend became unavailable. Missing metric messages remain `None`; absent hand messages are never turned into zero-coordinate hands.
- Face and hand image points are normalized in the raw, unrotated, unmirrored camera image: top-left origin, +X right, +Y down. Face mesh points can be outside 0–1. Clip drawings, rather than clamping each point to a border.
- TrueDepth landmarks use `region="mesh"` and the ARKit vertex `index`. `position_face_meters` is face-local meters (+X right, +Y up, +Z out of the face). `triangle_indices` references vertex IDs, not row numbers after filtering.
- Vision landmarks use region-local indices and named regions such as `face_contour`, `left_eye`, `outer_lips`. There is no topology or metric coordinate.
- `camera_position_meters` plus the quaternion `camera_orientation` transforms face-local vertices to ARKit camera space (+X right, +Y up, −Z forward). Quaternions are x,y,z,w.
- Source timestamps are monotonic seconds on the sender. `session_id` changes on restart; `sequence_number` counts captured frames. The independent hand stream has its own analyzed image source time. Do not assume equal timestamps or frame-for-frame alignment across the two streams.
- Each hand contains confidence and up to 21 named joints; low-confidence joints can be absent. Left/right are the app's anatomical convention, independent of preview mirroring. `unknown_hand_count` records detections that could not be assigned.

## Body

The [illustrated body guide](body-tracking.md) defines the complete native ARKit and MediaPipe payloads and their shared human API. ARKit sends the complete 91-node name-to-transform dictionary, with model-space and parent-local transforms, parent names, direct-tracking flags and an optional world anchor. MediaPipe sends every detected person with a session-scoped ID and all 33 indexed landmarks, image/body/model coordinates, optional registered camera/world coordinates, visibility and presence. Per-landmark rotations are unavailable for MediaPipe.

Native MediaPipe matrices are column-major flattened arrays; the SDK reshapes them into conventional NumPy matrices. Source timestamps are iPhone monotonic seconds; frame timestamps are wall-clock seconds. World origins are scoped by `world_frame_id`. Missing world registration never falls back to a body-relative value. Low-confidence points are preserved and position/rotation availability have separate masks.

`BodyPose.BodyPoseMessage` is a separate 2D upper-body contract. It has relative joint positions/angles, confidence, JSON backup, detection FPS and frame ID. Its nested `upper_body.timestamp` is milliseconds, unlike the floating-point seconds used by other channels.

## Controller, motion and gripper

- Controller arrays and their original four-button ordering are preserved; current legacy `button_pressed` uses triangle, square, cross, circle. Full state includes both sticks, face button analog values, D-pad, shoulder/trigger/stick/system buttons, motion, controller name, connection and battery. Current stick axes use −1…1, neutral zero. No automatic rescaling is performed.
- IMU vectors are present only for active sensors. Accelerometer, gravity and user acceleration use CoreMotion G; angular rate is rad/s; magnetometer is microtesla. The app's current IMU generated schema emits fields 1–6. Python retains legacy field 7 `attitude` for old senders; it stays absent with the current sender, rather than showing a made-up zero quaternion.
- AirPods `rotation` is quaternion x,y,z,w, not Euler angles. `timestamp` is Float32 from the sender; the standalone AirPods view uses CoreMotion time. Treat it as a source value, not a precise Unix timestamp or synchronized cross-device clock.
- Gripper `angle` and `motor.angle_percent` are the app's percent command. `ClawFrame.motor` is absent if the message is absent. Timestamp is Float32 in the existing schema, so modern epoch times have coarse precision. The Python receiver preserves that wire precision.

## Watch

The active Watch app batches `watch_batch.Watch` samples about every 0.3 seconds and sends `watch_batch.WatchBatch` to the configured computer. The Python receiver accepts its HEAD warm-up and persistent HTTP/1.1 POST requests. `frame_count` must match `len(frames)`; it rejects malformed or mismatched batches rather than guessing a schema.

Attitude is x,y,z,w; rotation rate is rad/s. The current sender copies CoreMotion gravity and user acceleration directly, so the values are in **G**, despite older schema comments saying m/s². Sample and batch timestamps use wall-clock seconds. A legacy `Watch.Watch` sample has no timestamp; Python preserves missing time as 0 rather than substituting receipt time.

## Checked behavior

Synthetic regression fixtures are encoded both by original 0.1.4 Python descriptors and the actual app's SwiftProtobuf models. Local TCP tests cover every default ZeroMQ stream; HTTP tests cover Watch warm-up, batches, keep-alive, invalid data, queue bounds and shutdown. HEVC uses an independently encoded test image. These checks validate parsing and local transport, not iPhone/Watch reachability, physical TrueDepth accuracy or sustained wireless throughput.
