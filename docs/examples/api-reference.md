# Data Format and API

These signatures describe SDK **1.0.2**. Every linked example is a complete standalone Python file copied into its documentation page. See the [example index](index.md) for installation and manual runs.

## Choose the receiving class

Import classes from `asmagic`. Basic AR examples use `ARDataSubscriber(ip)`; the full signature is `ARDataSubscriber(ip, port=8000, hwm=32, conflate=False, verbose=False)`. Body Tracking requires `BodyTrackingDataSubscriber(ip, model="arkit" or "mediapipe", port=None, hwm=1, conflate=True, verbose=False)`. `CameraDataSubscriber(ip, port=8105, hwm=32, conflate=False, verbose=False)` uses the same decoded-frame queue defaults. The remaining ZeroMQ classes use `Class(ip, port=DEFAULT_PORT, hwm=1, conflate=True, verbose=False)`.

| Class | Default TCP port | `receive()` result | Complete examples |
|---|---:|---|---|
| `CameraDataSubscriber` | 8105 | `CameraFrame` | [Camera only](camera.md) |
| `ARDataSubscriber` | 8000 | `ARFrame` | [AR](ar.md) |
| `IMUDataSubscriber` | 8002 | `IMUFrame` | [IMU](imu.md) |
| `JoystickDataSubscriber` | 8020 | `JoystickFrame` | [Joystick](joystick.md) |
| `AirPodsDataSubscriber` | 8001 | `AirPodsFrame` | [AirPods](airpods.md) |
| `BodyTrackingDataSubscriber(model="arkit")` | 8100 | `BodyTrackingFrame` | [Body Tracking](../body-tracking.md), [examples](body.md) |
| `BodyTrackingDataSubscriber(model="mediapipe")` | 8104 | `BodyTrackingFrame` | [Body Tracking](../body-tracking.md), [examples](body.md) |
| `BodyPoseDataSubscriber` | 8010 | `BodyPoseFrame` | [2D upper body](upper_body.md) |
| `HandPoseDataSubscriber` | 8101 | `HandPoseFrame` | [Hands](hand.md) |
| `FaceDataSubscriber` | 8102 | `FaceFrame` | [Face](face.md) |
| `ClawDataSubscriber` | 5301 | `ClawFrame` | [Grippers](claw.md); pass `port=5401` for the second |

`ip` is the sender's IP/hostname, without `tcp://`. `hwm` is a positive queue limit; `conflate=True` keeps the latest pending message. Set `conflate=False` to retain queued messages up to the configured limits; this still does not guarantee lossless capture. `verbose=True` enables connection/decode diagnostics. Opening a receiver does not enable the App output.

## Unified receiving pattern

Use `sub = Class(...)`, then `try: while True: frame = sub.receive()`, and call `sub.close()` in `finally`. All public basic examples use this pattern. `receive()` waits for a valid frame and never returns `None`. Use `receive(timeout=...)` to handle timeouts. Both modes raise `StopIteration` on closure. `for frame in sub` and `with sub` remain supported.

## Shared ZeroMQ receiving methods

| API | Return / behavior | Example |
|---|---|---|
| `receive()` | Wait for one valid frame; closed receivers raise `StopIteration` | [Continuous AR](ar.md) |
| `receive(timeout=1000)` | Valid typed frame or `None` on timeout; StopIteration on closure | [Options and timeouts](common.md#example-1-receiving-with-a-timeout-and-status) |
| `for frame in sub` | Wait and yield frames until closed or interrupted | Supported compatibility API |
| `stream(timeout=1000, on_frame=None, *, plot=False, plot_options=None)` | Generator; callback and plot use the same yielded frame | [Processing function](common.md#example-2-process-a-received-frame), [body plot](body.md#example-4-display-all-people-in-separate-skeleton-panels) |
| `Class.decode(payload: bytes)`; body: `BodyTrackingFrame.from_bytes(payload, model=...)` | Decode a specified native schema without a socket; malformed data raises an exception | [Save and offline decode](common.md#example-6-decode-a-saved-typed-frame-without-a-socket) |
| `with Class(...) as sub` | Close the receiver on leaving the block | Supported compatibility API |
| `close()` | Cleanup in finally; safe to call again | [Cleanup](common.md#example-1-receiving-with-a-timeout-and-status) |

Timeout units are integer **milliseconds**: `0` polls immediately, `-1` or `None` waits indefinitely, positive values bound the wait for valid data. Iteration and `stream()` keep waiting after timeouts; they do not yield `None`. AR decode errors raise `RuntimeError`; other typed receivers skip recoverable decode failures within the same timeout budget and expose the error in `last_error` until valid data arrives. A received empty tracking frame is still a frame.

Read multiple fields from one received frame to keep them aligned. JPEG array decoding is on demand. AR receives and decodes HEVC on a dedicated thread, independently of display/user processing. RGB conversion is on demand. For AR, `conflate=True` replaces only already-decoded output and never conflates encoded reference packets; `conflate=False` retains at most `hwm` decoded frames, replacing the oldest on overflow. `received_frames` counts background wire reception, which can exceed the number returned by `receive()`. Each connection has its own decoder. After joining, packet loss or a session/configuration change, `color_array` returns `None` until a key frame is received. An isolated HEVC P-frame from offline `decode()` cannot be decoded without stream history.

| Receiver attribute | Meaning |
|---|---|
| `ip`, `port`, `address` | Configured sender and `tcp://...` address |
| `is_connected` | Local subscription is open; does not prove the sender is sending |
| `has_received_data` | At least one frame has decoded successfully |
| `received_frames` | Successfully received/decoded frame count |
| `last_received_at` | Local `time.monotonic()` receipt time or `None`; not sender observation time |
| `last_error` | Most recent decode error string, reset on a successful frame, or `None` |

All attributes are used in the [status example](common.md#example-1-subscriber-options-timeouts-status-and-automatic-cleanup).

`connect(ip, port=8000, **kwargs)` is an AR subscriber context manager. `subscribe(stream, ip, **kwargs)` creates the named typed receiver. `STREAMS` contains the ten ZeroMQ names and `StreamInfo.subscriber`, `.port`, `.message`, `.feature`. See [frame fields](ar.md#example-6-read-image-and-pose-fields) and [factory](common.md#example-3-discover-streams-and-subscribe-by-name).

## Camera-only frame

`CameraDataSubscriber` returns `CameraFrame` on TCP 8105. Read RGB uint8 arrays through
`color_array` or `color_upright`, as with `ARFrame`; `image` and `image_upright` remain aliases.
Read capture metadata through `timestamp`, `source_timestamp`,
`frame_id`, `width`, `height`, `image_rotation_quarter_turns_clockwise` and `rgb_codec_name`.
`color_bytes` retains encoded JPEG/HEVC bytes; `has_color_image` checks presence.
`image_bytes` and `has_image` remain aliases.
`show_images(window_name="Camera Image", upright=True)` displays one image and returns a boolean.
Process window events with `cv2.waitKey(1)` and close windows when finished.
The frame has no pose, intrinsics or depth properties. See [camera examples](camera.md).
The same HEVC continuity, queue and reset behavior described above applies to this receiver.

## AR frame and methods

RGB, depth, confidence, poses, intrinsics and frame information are printed in [AR example 1](ar.md#example-1-continuous-ar-data-reading).

| Field / property | Type / meaning |
|---|---|
| `timestamp`, `source_timestamp` | Float seconds; legacy sender clock / sender monotonic AR capture time |
| `frame_id` | Integer frame identity |
| `local_pose`, `global_pose` | NumPy `float32` arrays with shape `(7,)`: `[tx, ty, tz, qx, qy, qz, qw]`; position in meters, rotation as a quaternion; empty if absent |
| `velocity` | NumPy vector `[vx, vy, vz]`, m/s, or empty |
| `camera_intrinsics` | NumPy array of nine column-major values, or empty |
| `has_pose` | Whether either pose array is nonempty |
| `color_img`, `color_bytes` | Aliases for encoded JPEG or HEVC bytes, empty if absent |
| `depth_img` | Raw little-endian uint16 depth bytes |
| `rgb_width`, `rgb_height`, `depth_width`, `depth_height` | Image dimensions |
| `has_color_image`, `has_depth_image` | Encoded data presence flags |
| `color_array`, `color` | Aliases: decoded H×W×3 RGB uint8 array, or `None`; HEVC requires PyAV |
| `depth_array`, `depth` | Aliases: H×W uint16 array, or `None` |
| `depth_meters_per_unit` | Transmitted scale; zero on older messages uses 0.0001 m/unit |
| `depth_confidence`, `depth_confidence_array` | Raw bytes / H×W uint8 confidence (0 low, 1 medium, 2 high), or `None` for the absent array |
| `local_pose_matrix`, `global_pose_matrix` | Added 4×4 matrix properties; original pose arrays stay available |
| `camera_intrinsics_matrix` | Added 3×3 column-major intrinsics property; original `camera_intrinsics` stays available |
| `session_identifier` | Sender session identity |
| `shared_world_identifier`, `global_pose_is_shared` | Shared-world identity / availability; absent shared metadata does not establish a common world |
| `rgb_codec`, `rgb_codec_name` | Numeric codec / name: 0 or 1 JPEG, 2 HEVC; unknown values remain `unknown` |
| `rgb_codec_config` | Tuple of codec configuration NAL byte strings |
| `rgb_is_key_frame`, `rgb_nal_unit_header_length` | Key-frame flag / length-prefix bytes |
| `protobuf` | Generated `Phone.Phone` message of this frame |

| `ARFrame` method | Return / behavior |
|---|---|
| `show_color(window_name="Color Image")` | OpenCV window; `True` if an image was displayed, `False` if no image |
| `show_depth(window_name="Depth Image", colormap=None)` | Colorized OpenCV depth preview; default JET; boolean result |
| `show_images(show_color=True, show_depth=True, color_window="Color Image", depth_window="Depth Image")` | `(color_displayed, depth_displayed)` booleans; false switches disable each window |

`frame.show_images()` displays both available images by default. Use `show_depth=False` or `show_color=False` to disable an image. See [images](ar.md#example-2-optionally-display-color-and-depth) and [matrices](ar.md#example-4-positions-quaternions-and-matrices). Image display uses `cv2.waitKey()` and `cv2.destroyAllWindows()`. The color array is RGB; OpenCV drawing expects BGR. Malformed image/depth bytes can raise when an array is decoded.


Read all fields from one received frame, as in [AR example 1](ar.md#example-1-continuous-ar-data-reading).

### AR Pose Format

`local_pose` and `global_pose` contain camera position and rotation as NumPy `float32` arrays with shape `(7,)`.

**Order**: `[tx, ty, tz, qx, qy, qz, qw]`

* `tx`, `ty`, `tz`: camera position along the world X, Y, Z axes, in meters.
* `qx`, `qy`, `qz`, `qw`: camera rotation as a unitless quaternion, in **x, y, z, w** order.

`local_pose` uses the device's local AR-session world. `global_pose` uses the shared world when available, otherwise it equals `local_pose`. For multiple devices, check `global_pose_is_shared` and `shared_world_identifier` before comparing global poses.

`local_pose_matrix` and `global_pose_matrix` provide the same poses as `float32` `(4, 4)` matrices. The top-left 3×3 contains rotation, the first three entries of the last column are `tx`, `ty`, `tz` in meters, and the last row is `[0, 0, 0, 1]`. The raw pose arrays stay unchanged; a missing pose returns `None` for its matrix property.

In the App's Original coordinate mode, X points right, Y up, and Z backward; the camera looks along negative Z. Robotics mode uses X forward, Y left, Z up. The App applies the selected coordinate mode and offset before sending poses.

`camera_intrinsics` is a `float32` array with shape `(9,)`, stored column by column in this order: `[fx, 0, 0, 0, fy, 0, cx, cy, 1]`. `fx` and `fy` are horizontal and vertical focal lengths; `cx` and `cy` are the optical center's horizontal and vertical coordinates. All four use pixels. `camera_intrinsics_matrix` provides the same values as a `(3, 3)` matrix.

## IMU and AirPods

`IMUFrame.timestamp` is sender seconds. Received vectors retain their original three-element NumPy arrays and four-element `attitude`. An omitted sensor has the original zero fallback with `has_*` false; a received zero measurement has `has_*` true. The [all-sensors example](imu.md#example-1-read-all-available-imu-sensors) prints all sensor fields.

| IMU field | Shape / unit | Presence property |
|---|---|---|
| `accelerometer` | 3, G | `has_accelerometer` |
| `gyroscope` | 3, rad/s | `has_gyroscope` |
| `magnetometer` | 3, microtesla | `has_magnetometer` |
| `gravity` | 3, G | `has_gravity` |
| `user_acceleration` | 3, G | `has_user_acceleration` |
| `attitude` | 4, x/y/z/w, old senders only | `has_attitude` |

The current iPhone IMU sender omits attitude. Check `has_*` before using a reading. Read all fields from one received frame in the [IMU example](imu.md#example-1-read-all-available-imu-sensors). `protobuf` retains the original message.

`AirPodsFrame.timestamp` is the Float32 source value; it is not a precise synchronized Unix time. `rotation` is a NumPy quaternion `[qx, qy, qz, qw]` (or an empty array), not Euler angles. `protobuf` retains the message. [Complete example](airpods.md).

## Controller

Named controls and original numbered fields are shown on the [Joystick page](../joystick.md).

| `JoystickFrame` member | Meaning |
|---|---|
| `button` | `JoystickButtons`; face, shoulder, D-pad, stick-click and system booleans; L2/R2 floats from 0.0 to 1.0. [Every named control](../joystick.md) |
| `timestamp`, `controller_name`, `is_connected` | Source seconds / controller name / controller connection state |
| `battery_level`, `is_charging` | Transmitted battery value / charging flag |
| `left_joystick`, `right_joystick` | Two-element NumPy arrays; current range −1…1 with neutral zero; older values unchanged |
| `left_stick`, `right_stick` | Aliases for the two arrays |
| `has_left_joystick`, `has_right_joystick` | At least two stick values exist |
| `left_x`, `left_y`, `right_x`, `right_y` | Scalar axis shortcuts; legacy fallback 0.5 if unavailable |
| `buttons`, `has_buttons` | Legacy boolean list / list is nonempty |
| `button1`, `button2`, `button3`, `button4` | Triangle, square, cross, circle; false if an entry is absent |
| `face_buttons` | Optional message with `triangle`, `square`, `cross`, `circle` and matching `*_value` analog values |
| `dpad` | Optional `up`, `down`, `left`, `right`, `axis.x`, `axis.y` |
| `shoulders` | Optional `l1`, `r1`, `l1_value`, `r1_value` |
| `triggers` | Optional `l2.value`, `l2.pressed`, `r2.value`, `r2.pressed` |
| `stick_buttons` | Optional `l3`, `r3` |
| `system_buttons` | Optional `menu`, `options`, `home`, `touchpad` |
| `motion` | Optional `sensors_active`, `gravity`, `user_acceleration`, `rotation_rate` (x/y/z), `attitude` (x/y/z/w) |
| `protobuf` | Generated message |


## Body tracking: ARKit and MediaPipe

Read full-body joint data from asMagic's **Body Tracking** feature. Use `BodyTrackingDataSubscriber(ip, model="mediapipe")` or `model="arkit"` to match the App setting. The model argument is required; default ports are 8104 for MediaPipe and 8100 for ARKit. Both return `BodyTrackingFrame`.

| Read | Result |
|---|---|
| `frame.people` | Every detected person in this frame; 0/1 for ARKit, 0–4 for the current MediaPipe model |
| `frame.person(person_id)` | Person with that session ID in this frame; `None` when absent |
| `frame.selected_person` | Optional App-selected MediaPipe target; other people remain available |
| `person.joints.left_shoulder`, `.right_elbow`, `.left_hip`, `.right_knee` | Named joints on both sides of the person's own body; unavailable joints are `None` |
| `person.skeleton()` | All 91 ARKit or 33 MediaPipe rows |
| `person.skeleton(layout="common")` | Twelve major joints on both arms and legs, with the same row order for both models |
| `person.skeleton(space="world")` | World positions; unavailable positions are NaN with `valid=False` |
| `skeleton.valid`, `skeleton.rotation_valid` | Position and rotation availability masks |
| `skeleton.usable` | Position available and model-specific quality criterion met; no rows are removed |
| `frame.timestamp` | Sender Unix seconds associated with the body frame |
| `frame.source_timestamp` | Source camera's monotonic seconds on the iPhone; a different clock |

MediaPipe provides joint positions and visibility/presence scores, but no joint rotations. Low-quality positions remain readable. ARKit distinguishes directly tracked joints from estimated nodes. MediaPipe person IDs are scoped to a session; ARKit's `"body"` ID represents one body slot and cannot identify a returning human.

See the [Body Tracking guide](../body-tracking.md) for runnable examples, coordinate spaces, units and missing-data behavior. The [joint catalog](joint-catalog.md) lists all twelve common rows, all 33 MediaPipe rows and all 91 ARKit rows with their Python paths and locations. Complete runnable files are on the [body examples page](body.md).

## 2D upper body

`BodyPoseFrame.upper_body` is an optional generated message; `json_data` is its string backup/metadata, `detection_fps` is sender detector FPS, `frame_id` is the sender frame ID and `protobuf` is the complete message. `.timestamp` aliases `upper_body.timestamp` in **milliseconds**, or 0 when upper body is absent.

`upper_body` contains `neck.x/y`, `left_arm`, `right_arm`, `confidence`, `timestamp`. Each arm contains relative `shoulder.x/y`, `elbow.x/y`, `wrist.x/y`, and `angles.elbow_angle`, `angles.shoulder_angle` in radians. Check `HasField()` for message presence. Relative origins differ; accumulate vectors before plotting the complete arm. Current detection membership is in `json_data.detected_joints` when supplied; field presence alone does not reject sender-filled old/default coordinates. [Fields and plot examples](upper_body.md).

## Hand frames and arrays

Every field is demonstrated on the [Hand page](hand.md). Joint mappings are in the [joint catalog](joint-catalog.md).

| Member | Meaning |
|---|---|
| `HandPoseFrame.source_timestamp`, `.timestamp` | Same monotonic source seconds |
| `.image_width`, `.image_height` | Raw image dimensions in pixels |
| `.left`, `.right` | Optional `Hand`; anatomical side, aliases of `.left_hand` / `.right_hand` |
| `.hands` | Tuple of assigned hands, left-then-right, omitting absent hands |
| `.has_left_hand`, `.has_right_hand`, `.hand_count` | Presence booleans / assigned-hand count |
| `.unknown_hand_count` | Detections with an unassigned side |
| `.protobuf` | Generated source message |
| `Hand.confidence` | Hand-level confidence |
| `Hand.side` | `HandSide.LEFT` / `RIGHT`; manually constructed hands default to `UNKNOWN` |
| `Hand.wrist`, `.thumb`, `.index`, `.middle`, `.ring`, `.little` | Read by anatomy: `hand.index.tip`; every node is optional |
| `HandFinger` / `HandThumb` | Non-thumb `mcp`, `pip`, `dip`, `tip`; thumb `cmc`, `mp`, `ip`, `tip` |
| `Hand.joints` | `HandJoints` dictionary with typed optional properties such as `.wrist`, `.index_tip` |
| `Hand.points` | Compact N×2 float32 of received points in dictionary order |
| `HandJoint.name`, `.x`, `.y`, `.confidence` | Wire name / normalized image point / joint confidence |
| `HandJoint.xy`, `.to_pixels(width, height)` | `(x, y)` tuple / continuous raw pixels; dimensions must be positive and finite |

`HandJointName` is a string enum with `.value` and `.row`. `HAND_JOINT_NAMES` lists all 21 names. `Hand.as_arrays()` returns `HandJointArrays(names, points, confidences, valid)`: `names` is `Tuple[str, ...]`; the other fields are NumPy arrays, with `points.shape == (21, 2)` and dtype `float32`, `confidences.shape == (21,)` and dtype `float32`, and `valid.shape == (21,)` and dtype `bool`. The first 21 rows are fixed; future names append alphabetically, increasing the row count to N. Missing points and confidences are NaN, `valid=False`. Presence and confidence filtering are separate. Use a new export after changing dictionaries; arrays are independent snapshots.

All hand coordinates are raw normalized image points, left-top origin, X right / Y down. They are **not 3D hand joints**. Left/right reflect the sender's anatomical side, independent of preview mirroring or screen position. The [hand guide with joint and reading diagrams](../hands.md) defines every node. See [all joints](hand.md#example-1-read-all-joints-from-both-hands), [typed/pixel access](hand.md#example-2-named-hand-joints-enums-and-raw-pixels) and [display switch](hand.md#example-3-enable-or-disable-both-hand-skeletons).

## Face-only frame

The [face guide](../face-and-hands.md) defines all 52 coefficients, nested landmark and bounding-box members, coordinate systems and missing-data rules, with text-free diagrams. [Runnable examples](face.md) inspect every returned type, read regions and convert mesh IDs and poses. `FaceFrame` has no hand members; receive [hands](hand.md) independently. See [migration notes](../compatibility.md#independent-face-and-hand-outputs) for old combined frames.

| Member | Python type / dtype / shape | Definition and missing value |
| --- | --- | --- |
| `source_timestamp` | `float` | Source camera capture time in monotonic seconds; wire `double`. |
| `timestamp` | `float` | Alias of `source_timestamp`. |
| `has_face` | `bool` | Whether a face was detected in this frame. |
| `image_width` | `int` | Original camera image width in pixels; wire `int32`, default 0. |
| `image_height` | `int` | Original camera image height in pixels; wire `int32`, default 0. |
| `image_location` | `FaceImageLocation` or `None` | Raw normalized face bounding box; [four scalar members](../face-and-hands.md). |
| `camera_position_meters` | float32 `np.ndarray`, `(3,)`, or `None` | Camera-relative `[x, y, z]` meters; TrueDepth only. |
| `camera_orientation` | float32 `np.ndarray`, `(4,)`, or `None` | Camera-relative `[qx, qy, qz, qw]` quaternion. |
| `blendshapes` | `dict[str, float]` | Named movement coefficients; empty `{}` when unavailable. |
| `blendshape_coefficients` | `dict[str, float]` | Alias returning the same dictionary as `blendshapes`. |
| `landmarks` | `tuple[FaceLandmark, ...]` | Received landmark records; empty `()` when unavailable. |
| `points` | float32 `np.ndarray`, `(N, 2)` | Derived raw image `[x, y]` rows; empty `(0, 2)`. |
| `face_vertices` | float32 `np.ndarray`, `(N, 3)`, or `None` | Derived face-local metric rows, present only when every landmark has a metric position. |
| `triangle_indices` | uint32 `np.ndarray`, `(3M,)` | Flat mesh vertex IDs; empty `(0,)`. |
| `triangles` | uint32 `np.ndarray`, `(M, 3)` | Three vertex IDs per triangle; empty `(0, 3)`. |
| `tracking_mode` | `str` | Decoded backend: `unspecified`, `vision`, `true_depth` or `unknown`. |
| `sequence_number` | `int` | Capture sequence within a session; wire `uint64`, older default 0. |
| `session_id` | `str` | Source capture session identifier; changes on restart, older default `""`. |
| `schema_version` | `int` | Transmitted schema version; current App uses 2, older default 0. |
| `protobuf` | Generated `asmagic.proto.face_tracking_pb2.FaceTrackingFrame` | Decoded message, descriptor `Phone.FaceTrackingFrame`; manually constructed `FaceFrame` can have `None`. |

`source_timestamp` is not Unix/UTC time and is not synchronized to the receiving computer. Use `session_id` with `sequence_number` to distinguish capture restarts. Old scalar defaults are not proof that the sender measured a zero. This face stream carries metadata and observations; it does not contain RGB/depth images, camera intrinsics or nested hands.

The wire field `blendshape_coefficients` is a repeated list of `FaceBlendshapeCoefficient` messages with `name: str` and `value: float`; the SDK converts it into the dictionary above. Wire position messages have float `x/y/z` members; the wire quaternion additionally has float `w`. The decoder converts those messages into float32 arrays in the documented order. Wire `landmarks` is a repeated message list; the SDK converts it into a tuple.

`FaceLandmark.index` is a Python `int`, `.region` is `str`, `.image_x` and `.image_y` are Python `float`, and `.position_face_meters` is float32 `(3,)` or `None`. TrueDepth indices are mesh vertex IDs; Vision indices are local to a region and can repeat. `FaceImageLocation.center_x`, `.center_y`, `.width` and `.height` are Python `float` in raw normalized image coordinates.

Face-local +X points to the viewer's right (the face's own left), +Y points up relative to the face, and +Z points out of the face. Camera axes are X right, Y up and −Z forward. For TrueDepth, transform a face-local point with `R(camera_orientation) @ point + camera_position_meters`. Vision has an estimated quaternion but no metric translation. [Mesh and camera conversion](face.md#example-3-metric-face-vertices-and-triangle-topology).

## Gripper

`ClawFrame.timestamp` is Float32 source time; `.angle` is the App percent command, `.motor` is a generated motor message or `None`, `.protobuf` is the complete generated message. The motor fields are `angle`, `angle_percent`, `speed`, `iq`, `temperature`; values are preserved as transmitted. See [first and second gripper examples](claw.md). No robot-control send method is implemented by these receiving classes.

## Watch HTTP

`WatchIMUReceiver(host="127.0.0.1", port=8002, conflate=True, max_batches=32, payload_format="batch", verbose=False)` starts an HTTP server on this computer. Use `host="0.0.0.0"` for LAN IPv4 clients; configure the Watch with this computer's reachable address, not the bind wildcard. `port=0` selects a free port. `payload_format` is `batch` (current), `single` (timestamped sample) or `legacy` (no timestamp). `conflate` selects latest-batch vs bounded queuing. Samples inside a retained batch are preserved.

| API / member | Meaning / return | Example |
|---|---|---|
| `receive()` | Wait for a WatchBatch; closed receivers raise StopIteration | [Batches](watch.md) |
| `receive(timeout=1000)` | `WatchBatch` or `None` on timeout; same timeout and closure behavior as ZeroMQ | [Batches](watch.md#example-1-receive-watch-http-batches-continuously) |
| Iteration | Yield batches until closed/interrupted | [Method selection](watch.md#example-3-watch-iteration-stream-callback-and-raw-protobuf) |
| `stream(timeout=1000, on_frame=None, *, plot=False, plot_options=None)` | Yield batches; callback receives that same batch; plot=True is unsupported | [Callback](watch.md#example-3-watch-iteration-stream-callback-and-raw-protobuf) |
| `iter_samples(timeout=1000)` | Flatten retained batches into `WatchFrame` samples | [Samples](watch.md#example-2-flatten-batches-into-individual-watch-samples) |
| `decode(payload)` | Instance method; parse selected schema into `WatchBatch` without dequeuing | [Formats and decode](watch.md#example-4-select-watch-payload-format-and-decode-a-batch) |
| `with receiver`, `close()` | Shutdown server and wake pending receive calls; examples close in finally | Every Watch example |
| `host`, `port`, `address` | Bound interface / actual port / HTTP endpoint |
| `payload_format` | Chosen input schema |
| `is_connected`, `has_received_data` | Server open / ever received a valid batch |
| `received_frames`, `dropped_batches` | Received batch count / discarded batch count |
| `last_received_at`, `last_error` | Local monotonic receipt time / validation error or `None` |

`WatchBatch.frames` is a tuple of `WatchFrame`, `.batch_timestamp` and `.timestamp` are aliases, `.frame_count` is the batch's count, `.protobuf` is its source message. `WatchFrame` fields are `timestamp` (sender seconds; legacy 0), `attitude` (x/y/z/w), `rotation_rate` (rad/s), `gravity` (G), `acceleration` (user acceleration in G), and `protobuf`. Vector fields are NumPy arrays. The actual current App sends G directly despite older schema comments saying m/s². [All sample fields](watch.md#example-1-receive-watch-http-batches-continuously).

## Plotting API

Supported objects: `BodyTrackingFrame`, `BodyPoseFrame`, `HandPoseFrame`, `FaceFrame`, `Hand`. Other streams cannot use `plot=True`; camera display has its separate image API. Default receiving plots are off. Matplotlib is installed with the SDK by default; run GUI plots on the main thread and choose Agg before importing pyplot for headless image export.

| API | Behavior / example |
|---|---|
| `sub.stream(..., plot=True, plot_options={...})` | Draw the same frame yielded; close window on generator close. Use `contextlib.closing` when breaking early. See body, upper-body, hand and face/hand optional plot examples. |
| `frame.plot(enabled=True, plotter=None, **options)` | Return a reusable plotter; disabled returns `None`. [Single-frame API](plotting.md#example-2-frameplot-or-plot_tracking-with-a-shared-window) |
| `hand.plot(enabled=True, plotter=None, **options)` | Same API for one hand. [Single-hand example](plotting.md#example-3-plot-a-single-hand-object) |
| `plot_tracking(frame, enabled=True, plotter=None, **options)` | Exported function equivalent to `.plot()`. [Function example](plotting.md#example-2-frameplot-or-plot_tracking-with-a-shared-window) |
| `TrackingPlotter(space="body", labels=False, max_fps=30, stale_after=2.0, min_confidence=0.0)` | Lazy reusable window. `"body"`/`"world"` accepted; `"parent"` rejected because parent origins differ. [Manual viewer](plotting.md#example-1-receive-frames-with-an-optional-trackingplotter) |
| `HandTrackingWindow(labels=True, max_fps=30, stale_after=2.0, min_confidence=0.0)` | Open anatomical L/R panels; `update(HandPoseFrame)` or `update(None)` on timeouts |
| `update(frame, force=False)` | Update using an already received frame; return self; no data receive/mutation. `force=True` bypasses draw throttling. |
| `idle()` | Process events and clear old data after `stale_after` during timeouts |
| `is_open` | Window still open, or lazy viewer awaiting its first update |
| `save(path, **savefig_options)` | Save current figure after its first update. [Headless snapshot](plotting.md#example-4-save-a-real-received-skeleton-without-a-window) |
| `close()`, context manager | Window cleanup |
| `space`, `labels`, `max_fps`, `stale_after` | Configured coordinate space / node labels / drawing FPS / stale seconds |
| `figure`, `axes` | Matplotlib figure (initially `None`) and axes list for custom styling after the first update; see the headless snapshot example |

One plotter accepts one kind of object. Set options at creation; supplying both an existing plotter and new options to `.plot()` / `plot_tracking()` raises `ValueError`. Do not create a new plotter every frame. BODY plots show model-space meters and real parent edges; WORLD plots require world metadata. Hands use anatomical separate panels with raw 2D coordinates, confidence coloring and no links across missing nodes. Face/hand plots add raw face landmarks. Upper-body plots accumulate relative vectors and use available detection metadata. Drawing limits affect visualization only, not the sender's configured frame rate.

## Generic and legacy schemas


`asmagic.proto` includes the generated camera, IMU, controller, AirPods, body, upper-body, hand, face/hand, gripper and Watch schemas. Raw payloads require matching schemas and transports. This SDK does not convert separate JSON/UDP/robot-command/control protocols into these Protobuf streams.
