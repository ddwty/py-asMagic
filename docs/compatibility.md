# Upgrading from 0.1.x

## Preserved

- Package name `asmagic` and imports of `ARDataSubscriber`, `IMUDataSubscriber`, `JoystickDataSubscriber`.
- The existing camel-case module paths: `asmagic.arDataSubscriber`, `asmagic.imuDataSubscriber`, `asmagic.joystickDataSubscriber`.
- Constructor argument order `ip, port, hwm, conflate, verbose` and original default ports.
- Iteration, context managers and `close`.
- Received frame fields and NumPy array values. Old pose arrays and controller axis values are returned unchanged.
- Camera/joystick original field numbers. Old packets can be decoded with their original semantics; unavailable new metadata retains empty/zero defaults.
- `ARFrame` matrix properties interpret a legacy 16-element array in row order, and now also supports the current seven-element translation/quaternion format.
- `local_pose_matrix`, `global_pose_matrix`, and `camera_intrinsics_matrix` are additional properties. Original `local_pose`, `global_pose` and `camera_intrinsics` arrays remain available.

`asmagic.subscriber` provides a compatibility import for the original AR-only module. `connect` is available both from `asmagic.arDataSubscriber` and the package root.

AR and IMU use `frame = sub.receive()` followed by direct field access. `frame.depth` keeps the original uint16 array; matrix properties expose the existing pose conversion.

## Corrections that may be visible

1. **IMU presence:** received vectors retain the original three-element arrays and four-element `attitude`, including the zero fallback for an omitted sensor. `has_*` checks Protobuf presence, so missing placeholders remain distinguishable from present zero measurements without changing field names or array shapes. Default-constructed frames retain their original empty arrays and length-based flags. Current iPhone output does not send attitude; the legacy field remains supported when present.
2. **Stick range documentation:** the latest sender uses −1…1, neutral zero. Values were always delivered verbatim; they still are. The old README's universal 0–1 claim has been corrected. Default-constructed `JoystickFrame()` retains its original 0.5 fallbacks.
3. **Images:** `color_bytes` can be HEVC in the new app. Use `rgb_codec_name` before saving bytes to a file, or use `color_array` to decode. JPEG and HEVC dependencies are included in the default SDK installation. Malformed image/depth buffers raise a descriptive exception on array access instead of being silently treated as a valid image.
4. **Socket state:** `is_connected` keeps its meaning as an open local subscription. It is now documented explicitly; actual receipt is exposed separately. `close()` uses zero linger to avoid waiting for queued network work.
5. **Protobuf dependency:** the old generated files required a newer runtime than the `protobuf>=4.0.0` metadata admitted. This update generates portable descriptor-builder bindings and requires `protobuf>=4.25.0`. It retains Python 3.8 support and isolates schemas from independently generated legacy modules.

## New fields are additive

Use `frame = sub.receive()` once, then read its properties to access a coherent message.

New face/body/hand subscribers follow the same receive pattern. Missing nested messages use `None`. No implicit transport negotiation, pairing, joint relabeling, controller rescaling or timestamp synchronization is added.

Body and hand `joints` now use dictionary subclasses with typed optional attributes and string enums. Existing string keys, dictionary iteration/mutation and `Hand.points` retain their behavior. New `ARBodyFrame.skeleton()` and `Hand.as_arrays()` exports have fixed canonical rows with NaN for missing joints; this padding is explicit and does not change the received dictionaries. Unknown future keys remain in the dictionaries and are appended to the bulk exports. Protocol schemas, packet bytes and source coordinate semantics are unchanged by these convenience APIs.

The sibling `joystickmagic/` package and old standalone scripts are retained separately. They are not required by the current `asmagic` package, and upgrading `asmagic` does not replace an installed `joystickmagic` package. The descriptor pools allow both to be imported together.

## Checks before using a device

The automated suite covers old descriptor fixtures, current Swift-encoded camera/controller/face fixtures, all default local TCP channels and Watch HTTP batches. Physical camera quality, anatomical handedness, network reachability, app permissions and wireless throughput must be checked with the sender device. A successful synthetic test is not evidence that a device is connected.

## Joystick input queries

`frame.button` adds named controls without changing old fields: ordinary buttons are bool, L2/R2 are 0.0–1.0 floats. It is also available for legacy and on-screen packets, with absent controls released.

The added pygame-style methods read one already-received frame. Original `left_x/y`, `right_x/y`, `buttons`, `button1`…`button4` and nested structures keep their values and ordering. Only the new `get_axis()` uses down-positive stick Y and −1…1 trigger axes. The new button indices follow a fixed PS5 layout; use `BUTTON_A`…`BUTTON_D` for the App screen labels. Virtual and physical frames expose identical logical control counts, with absent additional controls released. See [mapping](joystick.md).

## Independent face and hand outputs

Current App output is `Phone.HandPoseFrame` on 8101 and `Phone.FaceTrackingFrame` (schema version 2) on 8102. Use `HandPoseDataSubscriber` and `FaceDataSubscriber` independently. `subscribe("hand", ip)` and `subscribe("face", ip)` select these streams. Open only the receiver you need; enable and send only that tracking type in the App.

The face schema keeps its face field numbers and reserves former hand field 10. The SDK retains the legacy `FaceAndHandTrackingDataSubscriber`, `FaceAndHandTrackingFrame` and `subscribe("face_hand", ip)` for older App combined packets. Current App 8102 packets decode through the old class with `hands=None`; that class no longer gives hands from a new App. Read hands separately on 8101. A new FaceDataSubscriber can read older face fields while its protobuf object preserves unknown fields, but its public frame never exposes hands. Upgrade the App for independent recognition/output controls. See [face examples](examples/face.md) and [hand examples](examples/hand.md).
