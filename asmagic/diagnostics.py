"""Finite device probes and field checks; reception is not a claim of sensor accuracy."""
from collections import Counter
from dataclasses import dataclass, field
import math
import time
from typing import Dict, List

import numpy as np


@dataclass
class FrameInspection:
    components: Dict[str, bool]
    values: dict
    errors: List[str] = field(default_factory=list)

    @property
    def usable(self):
        return any(self.components.values()) and not self.errors


def inspect_frame(stream: str, frame, decode_images: bool = False) -> FrameInspection:
    """Check received fields without taking another frame or substituting missing data."""
    components, values, errors = {}, {}, []
    if not math.isfinite(frame.timestamp):
        errors.append("timestamp: nonfinite value")

    def vector(name, array, length):
        array = np.asarray(array)
        if array.size == 0:
            components[name] = False
        elif array.shape != (length,) or not np.isfinite(array).all():
            errors.append("{}: expected {} finite values".format(name, length))
            components[name] = False
        else:
            components[name] = True
            values[name] = array.tolist()

    if stream == "camera":
        components["rgb"] = frame.has_image
        values.update(frame_id=frame.frame_id, rgb_codec=frame.rgb_codec_name,
                      rgb_bytes=len(frame.image_bytes), width=frame.width, height=frame.height,
                      source_timestamp=frame.source_timestamp,
                      image_rotation_quarter_turns_clockwise=frame.image_rotation_quarter_turns_clockwise)
        if frame.has_image and decode_images:
            try:
                image = frame.image
                components["rgb_decoded"] = image is not None
                if image is None:
                    values["rgb_waiting_for_key_frame"] = True
                else:
                    values["rgb_shape"] = list(image.shape)
            except (ValueError, RuntimeError, ImportError, OSError) as error:
                errors.append("rgb: " + str(error))
    elif stream == "ar":
        values.update(frame_id=frame.frame_id, rgb_codec=frame.rgb_codec_name,
                      rgb_bytes=len(frame.color_img), depth_bytes=len(frame.depth_img))
        for name in ("local_pose", "global_pose"):
            pose = getattr(frame, name)
            components[name] = bool(pose.size)
            if pose.size:
                try:
                    matrix = getattr(frame, name + "_matrix")
                    if matrix is None or not np.isfinite(matrix).all():
                        raise ValueError("expected a finite 7-value pose or 16-value matrix")
                    values[name] = pose.tolist()
                except ValueError as error:
                    components[name] = False
                    errors.append(name + ": " + str(error))
        components["rgb"] = frame.has_color_image
        components["depth"] = frame.has_depth_image
        if frame.color_img and decode_images:
            try:
                image = frame.color_array
                components["rgb_decoded"] = image is not None
                if image is None:
                    values["rgb_waiting_for_key_frame"] = True
                else:
                    values["rgb_shape"] = list(image.shape)
            except (ValueError, RuntimeError, ImportError, OSError) as error:
                errors.append("rgb: " + str(error))
        if frame.depth_img:
            try:
                if not frame.has_depth_image:
                    raise ValueError("missing depth dimensions")
                values["depth_shape"] = list(frame.depth_array.shape)
                values["valid_depth_pixels"] = int(np.count_nonzero(frame.depth_array))
                if frame.depth_confidence:
                    _ = frame.depth_confidence_array
                    components["depth_confidence"] = True
            except ValueError as error:
                components["depth"] = False
                errors.append("depth: " + str(error))
        vector("velocity", frame.velocity, 3)
        vector("camera_intrinsics", frame.camera_intrinsics, 9)
    elif stream == "imu":
        for name in ("accelerometer", "gyroscope", "magnetometer", "gravity", "user_acceleration", "attitude"):
            if getattr(frame, "has_" + name):
                vector(name, getattr(frame, name), 4 if name == "attitude" else 3)
            else:
                components[name] = False
    elif stream == "airpods":
        vector("rotation", frame.rotation, 4)
        if components["rotation"] and np.linalg.norm(frame.rotation) == 0:
            errors.append("rotation: zero quaternion")
    elif stream == "joystick":
        vector("left_stick", frame.left_joystick, 2)
        vector("right_stick", frame.right_joystick, 2)
        components["buttons"] = bool(frame.buttons)
        values.update(buttons=frame.buttons, named_buttons=vars(frame.button),
                      controller=frame.controller_name, is_connected=frame.is_connected)
        for name in ("face_buttons", "dpad", "shoulders", "triggers", "stick_buttons", "system_buttons", "motion"):
            components[name] = getattr(frame, name) is not None
        if frame.triggers is not None:
            values["triggers"] = [frame.triggers.l2.value, frame.triggers.r2.value]
    elif stream == "ar_body":
        values.update(tracking_state=frame.tracking_state, session_id=frame.session_id,
                      joints=len(frame.joints), local_joints=len(frame.local_joints), parents=len(frame.joint_parents))
        components.update(body=frame.is_tracking and bool(frame.joints), local=bool(frame.local_joints),
                          world=frame.body_transform is not None, tracking_flags=bool(frame.tracked_joints))
        for space, joints in (("body", frame.joints), ("parent", frame.local_joints)):
            for name, joint in joints.items():
                if not np.isfinite(joint.position).all() or not np.isfinite(joint.rotation).all() or np.linalg.norm(joint.rotation) == 0:
                    errors.append("{} joint {}: nonfinite transform or zero quaternion".format(space, name))
        if frame.body_transform is not None:
            try:
                if not np.isfinite(frame.body_transform.matrix).all():
                    errors.append("body_transform: nonfinite transform")
            except ValueError as error:
                errors.append("body_transform: " + str(error))
    elif stream == "body_pose":
        from .plotting import upper_body_points
        _, _, valid, _, known = upper_body_points(frame)
        components["upper_body"] = bool(valid.any())
        values.update(points=int(valid.sum()), detection_flags_available=known, detection_fps=frame.detection_fps,
                      frame_id=frame.frame_id, timestamp_ms=frame.timestamp)
    elif stream in ("hand", "face", "face_hand"):
        for side in (() if stream == "face" else ("left_hand", "right_hand")):
            hand = getattr(frame, side)
            components[side] = hand is not None and bool(hand.joints)
            values[side + "_joints"] = len(hand.joints) if hand is not None else 0
            if hand is not None:
                for joint in hand.joints.values():
                    if not all(math.isfinite(v) for v in (joint.x, joint.y, joint.confidence)) or not 0 <= joint.confidence <= 1:
                        errors.append(side + "/" + joint.name + ": invalid point/confidence")
        if stream in ("face", "face_hand"):
            components.update(face=frame.has_face and bool(frame.landmarks), blendshapes=bool(frame.blendshapes),
                              mesh=frame.face_vertices is not None)
            values.update(has_face=frame.has_face, tracking_mode=frame.tracking_mode,
                          face_points=len(frame.landmarks), blendshapes=len(frame.blendshapes),
                          sequence_number=frame.sequence_number, session_id=frame.session_id,
                          hand_source_timestamp=frame.hands.timestamp if stream == "face_hand" and frame.hands else None)
            if any(not math.isfinite(value) or not 0 <= value <= 1 for value in frame.blendshapes.values()):
                errors.append("blendshapes: expected finite 0..1 coefficients")
            if not np.isfinite(frame.points).all():
                errors.append("face: nonfinite image points")
            if frame.face_vertices is not None and not np.isfinite(frame.face_vertices).all():
                errors.append("mesh: nonfinite vertices")
            if len(frame.triangle_indices) % 3:
                errors.append("mesh: triangle indices are not groups of three")
    elif stream in ("claw", "claw2"):
        components.update(command=bool(frame.protobuf.ListFields()), motor=frame.motor is not None)
        values.update(angle=frame.angle, motor_angle=frame.motor.angle_percent if frame.motor else None)
        if not math.isfinite(frame.angle):
            errors.append("angle: nonfinite value")
    elif stream == "watch":
        components["samples"] = bool(frame.frames)
        values.update(samples=len(frame.frames), batch_timestamp=frame.batch_timestamp)
        observed = {}
        for sample in frame.frames:
            for name in ("attitude", "rotation_rate", "gravity", "acceleration"):
                vector(name, getattr(sample, name), 4 if name == "attitude" else 3)
                observed[name] = observed.get(name, False) or components[name]
        components.update(observed)
    else:
        raise ValueError("Unknown stream: " + stream)
    return FrameInspection(components, values, errors)


@dataclass
class StreamTestResult:
    stream: str
    address: str
    status: str = "no_data"
    frames: int = 0
    usable_frames: int = 0
    samples: int = 0
    elapsed_seconds: float = 0.0
    received_fps: float = 0.0
    component_frames: dict = field(default_factory=dict)
    last_values: dict = field(default_factory=dict)
    errors: list = field(default_factory=list)
    manual_observation: str = "not_checked"


def run_stream_check(stream, receiver, duration=15.0, plot=False, plot_options=None,
                     images=False, count=0, on_status=None):
    """Read one stream for a finite period. Never equate an open socket with receipt."""
    if not math.isfinite(duration) or duration <= 0 or count < 0:
        raise ValueError("duration must be positive and count must be nonnegative")
    from .plotting import TrackingPlotter, _pyplot
    plotter = None
    if plot and stream in ("ar_body", "body_pose", "hand", "face", "face_hand"):
        _pyplot()
        plotter = TrackingPlotter(**(plot_options or {}))
    result = StreamTestResult(stream, receiver.address)
    components = Counter()
    start = last_print = time.monotonic()
    cv2 = None
    windows = ("asMagic RGB test", "asMagic depth test")

    def record(error):
        message = str(error)
        if message and message not in result.errors:
            result.errors.append(message)

    try:
        while time.monotonic() - start < duration and receiver.is_connected:
            if plotter is not None and not plotter.is_open:
                result.manual_observation = "window_closed"
                break
            remaining = duration - (time.monotonic() - start)
            wait = min(50 if plotter is not None or images else 250, max(0, int(remaining * 1000)))
            try:
                frame = receiver.receive(timeout=wait)
            except StopIteration:
                break
            except RuntimeError as error:
                record(error)
                frame = None
            if receiver.last_error:
                record(receiver.last_error)
            now = time.monotonic()
            if frame is not None:
                result.frames += 1
                result.samples += len(frame.frames) if stream == "watch" else 1
                inspection = inspect_frame(stream, frame, decode_images=stream in ("ar", "camera") and (result.frames == 1 or now - last_print >= 1))
                result.usable_frames += int(inspection.usable)
                components.update(name for name, present in inspection.components.items() if present)
                result.last_values = inspection.values
                for error in inspection.errors:
                    record(error)
                if plotter is not None:
                    plotter.update(frame)
                if images and stream in ("ar", "camera"):
                    import cv2
                    try:
                        if stream == "camera":
                            frame.show_images(window_name=windows[0])
                        else:
                            frame.show_images(color_window=windows[0], depth_window=windows[1])
                    except (ValueError, RuntimeError, ImportError, OSError) as error:
                        record(error)
                if count and result.frames >= count:
                    break
            elif plotter is not None:
                plotter.idle()
            if cv2 is not None and cv2.waitKey(1) & 0xff in (27, ord("q")):
                break
            if on_status is not None and now - last_print >= 1:
                on_status(result)
                last_print = now
    except KeyboardInterrupt:
        result.manual_observation = "interrupted"
    finally:
        if plotter is not None:
            plotter.close()
        if cv2 is not None:
            for name in windows:
                try:
                    cv2.destroyWindow(name)
                except cv2.error:
                    pass
    result.elapsed_seconds = time.monotonic() - start
    result.received_fps = result.frames / result.elapsed_seconds if result.elapsed_seconds else 0
    result.component_frames = dict(components)
    result.status = ("received_with_errors" if result.usable_frames and result.errors else "received" if result.usable_frames
                     else "errors" if result.errors else "empty_data" if result.frames else "no_data")
    return result
