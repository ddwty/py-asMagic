"""One protobuf-to-frame conversion per supported wire contract."""
import numpy as np

from .data_types import ARFrame, IMUFrame, JoystickFrame
from .camera_types import CameraFrame
from .joints import HandSide
from .tracking_types import (ARBodyFrame, AirPodsFrame, BodyPoseFrame, ClawFrame,
                             FaceAndHandTrackingFrame, FaceFrame, FaceImageLocation, FaceLandmark,
                             Hand, HandJoint, HandPoseFrame, JointTransform,
                             WatchFrame, WatchBatch)


def vector(message, names=("x", "y", "z")):
    return np.array([getattr(message, name) for name in names], dtype=np.float32)


def optional_message(message, name):
    return getattr(message, name) if message.HasField(name) else None


def ar_frame(message):
    return ARFrame(
        timestamp=message.timestamp, color_img=message.color_img, depth_img=message.depth_img,
        depth_width=message.depth_width, depth_height=message.depth_height,
        local_pose=np.array(message.local_pose, dtype=np.float32),
        global_pose=np.array(message.global_pose, dtype=np.float32),
        velocity=np.array(message.velocity, dtype=np.float32),
        camera_intrinsics=np.array(message.camersIntrinsics, dtype=np.float32),
        frame_id=message.frame_id, source_timestamp=message.source_timestamp,
        rgb_width=message.rgb_width, rgb_height=message.rgb_height,
        depth_confidence=message.depth_confidence, depth_meters_per_unit=message.depth_meters_per_unit,
        session_identifier=message.session_identifier, shared_world_identifier=message.shared_world_identifier,
        global_pose_is_shared=message.global_pose_is_shared,
        rgb_codec=message.rgb_codec, rgb_codec_config=tuple(message.rgb_codec_config),
        rgb_is_key_frame=message.rgb_is_key_frame,
        rgb_nal_unit_header_length=message.rgb_nal_unit_header_length, protobuf=message)


def camera_frame(message):
    return CameraFrame(
        timestamp=message.timestamp, source_timestamp=message.source_timestamp,
        frame_id=message.frame_id, color_img=message.color_img,
        rgb_width=message.rgb_width, rgb_height=message.rgb_height,
        rgb_codec=message.rgb_codec, rgb_codec_config=tuple(message.rgb_codec_config),
        rgb_is_key_frame=message.rgb_is_key_frame,
        rgb_nal_unit_header_length=message.rgb_nal_unit_header_length, protobuf=message)


def imu_frame(message):
    fields = {}
    for name in ("accelerometer", "gyroscope", "magnetometer", "gravity", "user_acceleration", "attitude"):
        # Preserve 0.1.x vector shapes, including Protobuf's zero fallback.
        fields[name] = vector(getattr(message, name), ("x", "y", "z", "w") if name == "attitude" else ("x", "y", "z"))
    return IMUFrame(timestamp=message.timestamp, protobuf=message, **fields)


def joystick_frame(message):
    left = np.array(message.l_joystick_position, dtype=np.float32)
    right = np.array(message.r_joystick_position, dtype=np.float32)
    # Preserve legacy arrays verbatim. New senders normally send both versions.
    if left.size == 0 and message.HasField("left_stick"):
        left = vector(message.left_stick, ("x", "y"))
    if right.size == 0 and message.HasField("right_stick"):
        right = vector(message.right_stick, ("x", "y"))
    buttons = list(message.button_pressed)
    if not buttons and message.HasField("face_buttons"):
        buttons = [getattr(message.face_buttons, name) for name in ("triangle", "square", "cross", "circle")]
    sections = {name: optional_message(message, name) for name in
                ("face_buttons", "dpad", "shoulders", "triggers", "stick_buttons", "system_buttons", "motion")}
    return JoystickFrame(timestamp=message.timestamp, left_joystick=left, right_joystick=right,
                         buttons=buttons, controller_name=message.controller_name,
                         is_connected=message.is_connected, battery_level=message.battery_level,
                         is_charging=message.is_charging, protobuf=message, **sections)


def hand(message, side=HandSide.UNKNOWN):
    return Hand(confidence=message.confidence, side=side, joints={joint.name: HandJoint(
        joint.name, joint.x, joint.y, joint.confidence) for joint in message.joints})


def hand_frame(message):
    return HandPoseFrame(
        source_timestamp=message.source_timestamp, image_width=message.image_width,
        image_height=message.image_height,
        unknown_hand_count=message.unknown_hand_count,
        left_hand=hand(message.left_hand, HandSide.LEFT) if message.HasField("left_hand") else None,
        right_hand=hand(message.right_hand, HandSide.RIGHT) if message.HasField("right_hand") else None, protobuf=message)


def face_frame(message):
    location = None
    if message.HasField("image_location"):
        p = message.image_location
        location = FaceImageLocation(p.center_x, p.center_y, p.width, p.height)
    landmarks = tuple(FaceLandmark(p.index, p.region, p.image_x, p.image_y,
                                   vector(p.position_face_meters) if p.HasField("position_face_meters") else None)
                      for p in message.landmarks)
    return FaceFrame(
        source_timestamp=message.source_timestamp, has_face=message.has_face,
        image_width=message.image_width, image_height=message.image_height,
        image_location=location,
        camera_position_meters=vector(message.camera_position_meters) if message.HasField("camera_position_meters") else None,
        camera_orientation=vector(message.camera_orientation, ("x", "y", "z", "w")) if message.HasField("camera_orientation") else None,
        blendshapes={p.name: p.value for p in message.blendshape_coefficients},
        landmarks=landmarks, triangle_indices=np.array(message.triangle_indices, dtype=np.uint32),
        tracking_mode={0: "unspecified", 1: "vision", 2: "true_depth"}.get(message.tracking_mode, "unknown"),
        sequence_number=message.sequence_number, session_id=message.session_id,
        schema_version=message.schema_version, protobuf=message)


def face_hand_frame(message):
    # Legacy decoder only; current face output carries no hand field.
    return FaceAndHandTrackingFrame(**vars(face_frame(message)),
        hands=hand_frame(message.hand_pose) if message.HasField("hand_pose") else None)


def joint_transform(message):
    return JointTransform(vector(message.position), vector(message.rotation, ("x", "y", "z", "w")))


def ar_body_frame(message):
    fields = {name: getattr(message, name) for name in (
        "timestamp", "left_arm_rotation", "left_arm_angle", "left_forearm_rotation", "left_forearm_angle",
        "right_arm_rotation", "right_arm_angle", "right_forearm_rotation", "right_forearm_angle",
        "tracking_state", "source_timestamp", "session_id", "estimated_scale")}
    for name in ("right_shoulder_1_pos", "right_arm_pos", "right_forearm_pos", "left_shoulder_1_pos", "left_arm_pos", "left_forearm_pos"):
        fields[name] = vector(getattr(message, name)) if message.HasField(name) else None
    return ARBodyFrame(
        joints={name: joint_transform(value) for name, value in message.joints.items()},
        local_joints={name: joint_transform(value) for name, value in message.local_joints.items()},
        joint_parents=dict(message.joint_parents), tracked_joints=dict(message.tracked_joints),
        body_transform=joint_transform(message.body_transform) if message.HasField("body_transform") else None,
        protobuf=message, **fields)


def body_pose_frame(message):
    return BodyPoseFrame(optional_message(message, "upper_body"), message.json_data,
                         message.detection_fps, message.frame_id, message)


def airpods_frame(message):
    return AirPodsFrame(message.timestamp, np.array(message.rotation, dtype=np.float32), message)


def claw_frame(message):
    return ClawFrame(message.timestamp, message.angle, optional_message(message, "motor"), message)


def watch_frame(message):
    return WatchFrame(getattr(message, "timestamp", 0.0), np.array(message.attitude, dtype=np.float32),
                      np.array(message.rotation_rate, dtype=np.float32), np.array(message.gravity, dtype=np.float32),
                      np.array(message.acceleration, dtype=np.float32), message)


def watch_batch(message):
    return WatchBatch(tuple(watch_frame(frame) for frame in message.frames), message.batch_timestamp,
                      message.frame_count, message)
